import subprocess, os, sys

wellknown_idls = ['BasicDataType.idl', 'InterfaceDataTypes.idl', 'ExtendedDataTypes.idl']

def copy_idl_and_compile(parser, idl_path):
    idl_dir = os.path.join('modules', 'idl')
    if not os.path.isdir(idl_dir):
        os.mkdir(idl_dir)

    copy_idl(parser, idl_path, idl_dir)
    compile_idl(parser, idl_dir)
    pass

def copy_idl(parser, idl_path, idl_dir):
    if os.path.basename(idl_path) in wellknown_idls:
        return True
    import shutil
    shutil.copy(idl_path, os.path.join(idl_dir, os.path.basename(idl_path)))

    included_paths = parser.includes(idl_path)
    for p in included_paths:
        copy_idl(parser, p, idl_dir)

def compile_idl(parser, idl_dir):
    cmd = ['omniidl', '-bpython']
    for dir in parser.dirs:
        if os.path.isdir(dir):
            cmd.append('-I%s' % dir)
        pass

    for p in os.listdir(idl_dir):
        if p.endswith('.idl'):
            cmd.append(os.path.join('idl', p))
    print cmd
    cwd = os.getcwd()
    os.chdir('modules')
    subprocess.call(cmd)
    os.chdir(cwd)
    
