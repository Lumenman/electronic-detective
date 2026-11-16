"""pygame-ce in place of python-for-android's own pygame recipe (2.1.0, which does not compile for Python 3.11+).
The body is that recipe's; only the version, the source and the Cython it needs differ."""
import glob
import shutil
from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class PygameCeRecipe(CompiledComponentsPythonRecipe):
    version = '2.5.8'
    url = 'https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz'

    site_packages_name = 'pygame'
    name = 'pygame'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']
    hostpython_prerequisites = ['setuptools', 'cython>=3.0,<=3.2.9']      # setup.py makes the C files itself
    call_hostpython_via_targetpython = False  # Due to setuptools
    install_in_hostpython = False
    build_cmd = 'build'                       # the Python files too: install_python_package() copies the result

    def install_python_package(self, arch, name=None, env=None, is_dir=True):
        """pip would build again, with meson, which pygame-ce does not support for Android: copy what is built."""
        with current_directory(self.get_build_dir(arch.arch)):
            built = glob.glob('build/lib.*/pygame')[0]
            target = join(self.ctx.get_python_install_dir(arch.arch), 'pygame')
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(built, target)

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            png = self.get_recipe('png', self.ctx)
            jpeg = self.get_recipe('jpeg', self.ctx)
            includes = lambda name: ''.join(
                f"-I{d} " for d in self.get_recipe(name, self.ctx).get_include_dirs(arch))
            open("Setup", "w").write(setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL', 'include') +
                    " -L" + join(self.ctx.bootstrap.build_dir, "libs", str(arch)) +
                    " -L" + join(png.get_build_dir(arch.arch), '.libs') +
                    " -L" + jpeg.get_build_dir(arch.arch) + " -L" + arch.ndk_lib_dir_versioned),
                sdl_ttf_includes="-I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_ttf'),
                sdl_image_includes=includes('sdl2_image'),
                sdl_mixer_includes=includes('sdl2_mixer'),
                jpeg_includes="-I" + jpeg.get_build_dir(arch.arch),
                png_includes="-I" + png.get_build_dir(arch),
                freetype_includes=""))

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL2'] = '1'
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = PygameCeRecipe()
