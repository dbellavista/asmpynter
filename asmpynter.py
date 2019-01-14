#!/usr/bin/env python2

import readline
import sys
import os
import math
from asmpynter.colorlog import ColorLog
from asmpynter.source import Source
from asmpynter.source import Instruction
from asmpynter.toolchain import Compiler, QemuExecutor, SystemExecutor, CodeGenerator
from asmpynter.status import RegStatusView
import ConfigParser
import asmpynter.toolchain

HISTORY_FILE = ".asmpyter_history"


class Asmpynter:

    def __init__(self, name, CodeGenerator, compiler, executor):
        self.source = Source()
        self.name = name
        self.codeGenerator = CodeGenerator
        self.compiler = compiler
        self.executor = executor

    def undo(self):
        self.source.remove_last_istruction()

    # def show(self):
        # print self.source

    def reset(self):
        self.source.clear_instructions()

    def exit(self):
        self.quit()

    def quit(self):
        self.source.clear_instructions()
        self.source = None
        self.name = None
        self.codeGenerator = None
        self.compiler = None
        self.executor = None

    def new_instruction(self, inst):
        inst = Instruction(inst)
        self.source.add_instruction(inst)

        sfile = self.codeGenerator.generate_as_list(self.source.source)
        (ok, err) = self.compiler.compile(sfile, True)
        if not ok:
            self.source.remove_last_istruction()
        return (ok, err)

    def execute(self):
        sfile = self.codeGenerator.generate_as_list(self.source.source)
        (exe_file, err) = self.compiler.compile(sfile)
        if not exe_file:
            return (None, err)
        (status, err_comp) = self.executor.execute(exe_file)
        return (status, err_comp)


def parse_command(command, asmpynter_i, cl):
    execute_source = True

    if command == "undo":
        asmpynter_i.undo()
    elif inst == "show":
        print asmpynter_i.source
        execute_source = False
    elif inst == "reset":
        asmpynter_i.reset()
    elif inst == "help":
        print_help(cl)
        execute_source = False
    elif inst == "exit" or inst == "quit":
        asmpynter_i.quit()
        print cl.enabled("Bye!")
        readline.write_history_file(HISTORY_FILE)
        execute_source = False
        sys.exit(0)
    else:
        (ok, err) = asmpynter_i.new_instruction(command)
        if not ok:
            print cl.fail(err)

    return execute_source


def print_banner(cl):
    print cl.header("Welcome to asm interpreter version 0.1!")
    print cl.header("Program by db")
    print ""


def print_help(cl):
    print cl.info("Insert the code, one instruction per line")
    print cl.info("""Extra commands:
  - help: show this message
  - undo: remove the last instruction
  - show: show the current source
  - reset: clean the program
  - quit/exit: exit
""")


def getCfg(cl, config, sect, name, req=False, additional='', checkFile=False):
    try:
        val = config.get(sect, name)
    except:
        val = None
    if val is None and req:
        print cl.error('Error in configuration: {0}.{1} is required{2}!'
                 .format(sect, name, additional))
        return None
    if val is not None and checkFile:
        if not checkExists(cl, val):
            return None
    return val


def getDict(cl, config, sect, name, req=False, additional=''):
    val = getCfg(cl, config, sect, name, req, additional)
    if val is None and req:
        return None
    elif val is None:
        return {}
    els = val.split(',')
    dictf = {}
    for el in els:
        kv = el.split(':')
        if len(kv) != 2:
            print cl.error(
                'Wrong format in {0}.{1} dictionary{2}.'.format(sec, name, additional))
            return None
        dictf[kv[0].strip()] = kv[1].strip()
    return dictf


def getList(cl, config, sect, name, req=False, additional=''):
    val = getCfg(cl, config, sect, name, req, additional)
    if val is None and req:
        return None
    elif val is None:
        return {}
    return [e.strip() for e in val.split(',') if len(e.strip()) > 0]


def checkExists(cl, path):
    if not os.path.isfile(path):
        print cl.error('File {0} was not found!'.format(path))
        return False
    return True


def parseArchitectures(cl, cfgFile):
    config = ConfigParser.ConfigParser()
    config.readfp(open(cfgFile))
    archs = []
    for an in config.sections():
        print cl.info('Parsing architecture {0}'.format(an))
        # Compiler and executor configuration
        comp = getCfg(cl, config, an, 'compiler', True, '', True)
        compilation_command = getCfg(
            cl, config, an, 'compilation_command', True)
        link_command = getCfg(cl, config, an, 'link_command', True)
        gdb = getCfg(cl, config, an, 'gdb', True, '', True)
        gdb_command = getCfg(cl, config, an, 'gdb_command', True)
        lib_path = getCfg(cl, config, an, 'lib_path', True)
        asm_template = getCfg(cl, config, an, 'asm_template', True, '', True)

        try:
            bb = int(getCfg(cl, config, an, 'bits', True))
            bits = int(math.ceil(bb / 8.0))
        except:
            print cl.error('Bits need to be a number greater than 0!')
            bits = None

        if comp is None or compilation_command is None\
                or link_command is None or gdb is None or gdb_command is None\
                or asm_template is None or lib_path is None or bits is None:
            continue

        # Code generator
        codeGen = CodeGenerator(asm_template)
        compiler = Compiler(comp, compilation_command, link_command)
        # Executor choice
        exec_command = getCfg(cl, config, an, 'exec_command')
        if exec_command is not None:
            # Exec mode
            executor = SystemExecutor(gdb, gdb_command, lib_path, exec_command)
        else:
            qemu = getCfg(cl, config, an, 'qemu', True,
                          ' if exec_command is not defined', True)
            qemu_port = getCfg(cl, config, an, 'qemu_port', True,
                               ' if exec_command is not defined')
            qemu_command = getCfg(cl, config, an, 'qemu_command', True,
                                  ' if exec_command is not defined')
            if qemu is None or qemu_port is None or lib_path is None:
                continue
            # Qemu mode
            executor = QemuExecutor(
                gdb, gdb_command, lib_path, qemu, qemu_command, qemu_port)

        # StatusViewer configuration
        rename_reg = getDict(cl, config, an, 'rename_register', False)
        blacklist_map = getDict(cl, config, an, 'blacklist_map', False)
        flag_register = getCfg(cl, config, an, 'flag_register', False)
        flag_names = getList(cl, config, an, 'flag_names', False)

        # Syntax error
        if rename_reg is None or blacklist_map is None:
            continue

        statusView = RegStatusView(
            rename_reg, blacklist_map, flag_register, flag_names, bits)

        archs.append(
            (an, codeGen, compiler, executor, statusView, HISTORY_FILE + '_' + an))
    return archs

if __name__ == '__main__':

    cl = ColorLog()
    print_banner(cl)

    archs = parseArchitectures(cl, './asmpynter.cfg')

    if len(archs) == 0:
        print cl.error(
            'No architectures could be parsed, check your configuration file!')
        sys.exit(1)
    archmap = {}
    for a in archs:
        name = a[0].lower()
        print cl.succeed('{0} architecture available'.format(name))
        archmap[name] = a
    an = None
    if len(sys.argv) >= 2:
        an = sys.argv[1]
    try:
        while an not in archmap:
            an = raw_input(' Select the architecture > ').lower()
    except EOFError:
        print ""
        print cl.info('Bye!')
        sys.exit(0)

    print ''
    arch = archmap[an]
    asmpynter_i = Asmpynter(arch[0], arch[1], arch[2], arch[3])
    print_help(cl)

    try:
        readline.read_history_file(arch[5])
    except IOError:
        with open(arch[5], 'w'):
            pass
        readline.read_history_file(arch[5])

    while 1:
        prompt = " " + cl.green("%03d" %
                                asmpynter_i.source.instructions_len()) + " > "
        try:
            inst = raw_input(prompt)
            readline.add_history(inst)
        except EOFError:
            print ""
            inst = "quit"
        if parse_command(inst, asmpynter_i, cl):
            (status, err) = asmpynter_i.execute()
            if status is not None:
                print cl.blue(arch[4].view(status))
            if err is not None:
                print cl.fail("Error: " + err)
