import tempfile
import re
import subprocess
import json
import os


class CodeGenerator:

    def __init__(self, template):
        with open(template) as f:
            self.template = f.read()
        ex = os.path.splitext(template)  # TODO (read doc!)
        if len(ex) != 2:
            raise Exception('Template must have an extension!')
        else:
            self.extension = ex[1]

    def generate_as_list(self, alist):
        res = ""
        for s in alist:
            res += '"{0}\\n"\n'.format(s)

        with tempfile.NamedTemporaryFile(prefix="source", suffix="." + self.extension, delete=False) as source_file:
            source_file.write(self.template.format(res))
        return source_file.name


class Compiler:

    def __init__(self, compiler, format_comp, format_link):
        self.compiler = compiler
        self.format_comp = format_comp
        self.format_link = format_link

    def compile(self, source_file, checkOnly=False):
        exe_file = tempfile.NamedTemporaryFile(prefix="exe", suffix=".out", delete=False)
        object_file = tempfile.NamedTemporaryFile(prefix="obj", suffix=".o", delete=False)
        ok, err = self._compile_and_link(source_file, object_file.name, exe_file.name, checkOnly)
        if checkOnly:
            return ok, err
        if ok:
            return (exe_file.name, None)
        return (None, err)

    def _compile_and_link(self, source_file, object_file, exe_file, delete_exe):

        err = self._compile(source_file, object_file)
        if err is None:
            err = self._link(object_file, exe_file)

        if os.path.exists(source_file):
            os.unlink(source_file)
        if os.path.exists(object_file):
            os.unlink(object_file)
        if os.path.exists(exe_file) and (delete_exe or err is not None):
            os.unlink(exe_file)
            exe_file = None

        return (err is None, err)

    def _compile(self, source_file, object_file):
        try:
            subprocess.check_output(self.format_comp.
                                    format(self.compiler, source_file,
                                           object_file),
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            err = e.output
            return err

    def _link(self, object_file, exe_file):
        try:
            subprocess.check_output(self.format_link.
                                    format(self.compiler, object_file,
                                           exe_file),
                                    stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            err = e.output
            return err


class Executor(object):

    def __init__(self, gdb, gdb_command, lib_path, remote_port=None):
        self.gdb = gdb
        self.gdb_command = gdb_command
        self.lib_path = lib_path
        self.remote_port = remote_port

    def execute(self, exe_file):
        err = None
        res = None

        # Creating the GDB files: commands and output log
        with tempfile.NamedTemporaryFile(prefix="gdb_cmds", suffix=".txt", delete=False) as gdb_cmd_file:
            with tempfile.NamedTemporaryFile(prefix="gdb_log", suffix=".txt", delete=False) as gdb_out:
                pass
            gdb_cmd_file.write('''
                               set loggin file {0}
                               set logging on
                               file {1}
                               set sysroot {2}
                               break __main_end
                               '''
                               .format(gdb_out.name, exe_file, self.lib_path)
                               )

            if self.remote_port is not None:
                gdb_cmd_file.write('''
                                   target remote localhost:{0}
                                   continue
                                   '''.format(self.remote_port))
            else:
                gdb_cmd_file.write('run\n')

            gdb_cmd_file.write('''
                               i r
                               continue
                               quit
                               ''')

        gdb_formatted = self.gdb_command.format(self.gdb, gdb_cmd_file.name,
                                                exe_file)
        try:
            (res, err) = self._execute(exe_file, gdb_formatted, gdb_out.name)
            return (res, err)
        except Exception as e:
            return (res, str(e))
        finally:
            if os.path.exists(exe_file):
                os.unlink(exe_file)
            if os.path.exists(gdb_cmd_file.name):
                os.unlink(gdb_cmd_file.name)
            if os.path.exists(gdb_out.name):
                os.unlink(gdb_out.name)

    def _execute(self, exe_file, gdb_formatted, gdb_out):
        raise NotImplementedError("To be implemented by derived executor")

    def _parse_gdb_output(self, lines):
        regs = False
        re_br = re.compile('^Breakpoint 1')
        re_reg = re.compile('(\w+)\s*0x([a-f0-9]+)')
        si_reg = re.compile('Program received signal (\w+), (.*)')

        final_regs = {}
        err = None

        for line in lines:
            if regs:
                res = re_reg.findall(line)
                if res is None or len(res) == 0:
                    regs = False
                    continue
                final_regs[res[0][0]] = int(res[0][1], 16)
            elif si_reg.match(line) is not None:
                err = si_reg.findall(line)[0][0]
            else:
                regs = re_br.match(line) is not None

        return final_regs, err


class SystemExecutor(Executor):

    def __init__(self, gdb, gdb_command, lib_path, exec_cmd):
        super(SystemExecutor, self).__init__(
            gdb, gdb_command, lib_path)
        self.exec_cmd = exec_cmd

    def _execute(self, exe_file, gdb_formatted, gdb_out):
        try:
            subprocess.check_output(self.exec_cmd.format(gdb_formatted),
                                    stderr=subprocess.STDOUT, shell=True)
            with open(gdb_out) as f:
                lines = f.readlines()
            status, err = self._parse_gdb_output(lines)
            return (status, err)
        except subprocess.CalledProcessError as e:
            try:
                status, rr = self._parse_gdb_output(e.output)
                err = "Return code: " + str(e.returncode)
                if rr is not None:
                    err = rr + '\n' + err
            except:
                status = None
                err = "Runtime Error! Return code: " + str(e.returncode)
                if len(e.output) > 0:
                    err += " (" + e.output + ")"
            return (status, err)


class QemuExecutor(Executor):

    def __init__(self, gdb, gdb_command, lib_path, qemu, qemu_command, qemu_port):
        super(QemuExecutor, self).__init__(
            gdb, gdb_command, lib_path, qemu_port)
        self.qemu = qemu
        self.qemu_command = qemu_command
        self.qemu_port = qemu_port

    def _execute(self, exe_file, gdb_formatted, gdb_out):
        try:
            qproc = subprocess.Popen([self.qemu_command.format(self.qemu, self.qemu_port, self.lib_path, exe_file)],
                                     stderr=subprocess.PIPE, stdout=None, shell=True)
            subprocess.check_output(gdb_formatted, stderr=subprocess.STDOUT, shell=True)
            qproc.kill()

            with open(gdb_out) as f:
                lines = f.readlines()
            status, err = self._parse_gdb_output(lines)
            return (status, err)
        except subprocess.CalledProcessError as e:
            err = "Return code: " + str(e.returncode)
            return (None, err)
        except Exception as e1:
            import traceback
            print e1
            traceback.print_exc()
            err = str(e1)
            return (None, err)
