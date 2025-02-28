import os
import re

from fnmatch import fnmatch
from conans import ConanFile, tools
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain
from pathlib import Path, PureWindowsPath


class VTKConan(ConanFile):
    name = "vtk"
    version = "9.4.1"
    description = "Visualization Toolkit by Kitware"
    url = "http://github.com/bilke/conan-vtk"
    license = "MIT"
    # generators = "cmake"
    generators = "CMakeDeps"
    settings = "os", "compiler", "build_type", "arch"
    revision_mode = "scm"
    exports = [
        "LICENSE.md",
        "CMakeLists.txt",
        "FindVTK.cmake",
        "vtknetcdf_snprintf.diff",
        "vtktiff_mangle.diff",
    ]
    source_subfolder = "vtk"
    options = {
        "shared": [True, False],
        "qt": [True, False],
        "mpi": [True, False],
        "fPIC": [True, False],
        "minimal": [True, False],
        "ioxml": [True, False],
        "ioexport": [True, False],
        "mpi_minimal": [True, False],
        "ioxdmf3": [True, False],
        "iolegacy": [True, False],
        "basic_viewer": [True, False],
    }
    default_options = (
        "shared=True",
        "qt=True",
        "mpi=False",
        "fPIC=False",
        "minimal=False",
        "ioxml=False",
        "ioexport=False",
        "mpi_minimal=False",
        "ioxdmf3=False",
        "iolegacy=False",
        "basic_viewer=False",
    )

    short_paths = True

    version_split = version.split(".")
    short_version = "%s.%s" % (version_split[0], version_split[1])

    def source(self):
        tools.get(
            "https://github.com/Kitware/{0}/archive/v{1}.tar.gz".format(
                self.name.upper(), self.version
            )
        )
        extracted_dir = self.name.upper() + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)
        # tools.patch(
        #    base_path=self.source_subfolder, patch_file="vtknetcdf_snprintf.diff"
        # )
        # tools.patch(base_path=self.source_subfolder, patch_file="vtktiff_mangle.diff")

    def requirements(self):
        if self.options.ioxdmf3:
            self.requires("boost/1.66.0@conan/stable")
        if self.options.qt:
            self.requires("qt/6.8.2@lkeb/stable")
            # self.options["qt"].shared = True
            # if tools.os_info.is_linux:
            #    self.options["qt"].qtx11extras = True

    def _system_package_architecture(self):
        if tools.os_info.with_apt:
            if self.settings.arch == "x86":
                return ":i386"
            elif self.settings.arch == "x86_64":
                return ":amd64"

        if tools.os_info.with_yum:
            if self.settings.arch == "x86":
                return ".i686"
            elif self.settings.arch == "x86_64":
                return ".x86_64"
        return ""

    def build_requirements(self):
        pack_names = None
        if not self.options.minimal and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                pack_names = [
                    "freeglut3-dev",
                    "mesa-common-dev",
                    "mesa-utils-extra",
                    "libgl1-mesa-dev",
                    "libglapi-mesa",
                    "libsm-dev",
                    "libx11-dev",
                    "libxext-dev",
                    "libxt-dev",
                    "libglu1-mesa-dev",
                ]

        if pack_names:
            installer = tools.SystemPackageTool()
            for item in pack_names:
                installer.install(item + self._system_package_architecture())

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def _get_tc(self):
        """Generate the CMake configuration using
        multi-config generators on all platforms, as follows:

        Windows - defaults to Visual Studio
        Macos - XCode
        Linux - Ninja Multi-Config

        CMake needs to be at least 3.17 for Ninja Multi-Config

        Returns:
            CMakeToolchain: a configured toolchain object
        """
        generator = None
        if self.settings.os == "Macos":
            generator = "Xcode"

        if self.settings.os == "Linux":
            generator = "Ninja Multi-Config"

        tc = CMakeToolchain(self, generator=generator)
        tc.variables["BUILD_TESTING"] = "OFF"
        tc.variables["BUILD_EXAMPLES"] = "OFF"
        tc.variables["BUILD_SHARED_LIBS"] = "TRUE" if self.options.shared else "FALSE"

        # Locate qt and add path to cmake prefix to allow lib discovery
        qt_path = Path(self.deps_cpp_info["qt"].rootpath)
        qt_cfg = list(qt_path.glob("**/Qt6Config.cmake"))[0]
        qt_dir = qt_cfg.parents[0].as_posix()
        qt_root = qt_cfg.parents[2].as_posix()

        # for qt & ads
        tc.variables["Qt6_ROOT"] = qt_root
        tc.variables["Qt6_DIR"] = qt_dir
        tc.variables["QT_DIR"] = qt_dir
        tc.variables["CMAKE_PREFIX_PATH"] = f"{qt_root}"
        print("Qt root ", qt_root)

        if self.options.basic_viewer:
            tc.variables["VTK_Group_StandAlone"] = "OFF"
            tc.variables["VTK_Group_Rendering"] = "OFF"
            tc.variables["VTK_ENABLE_WRAPPING"] = "OFF"
            tc.variables["VTK_MODULE_ENABLE_VTK_AcceleratorsVTKmCore"] = "DONT_WANT"
            tc.variables[
                "VTK_MODULE_ENABLE_VTK_AcceleratorsVTKmDataModel"
            ] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_AcceleratorsVTKmFilters"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_DomainsChemistry"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_DomainsChemistryOpenGL2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_DomainsMicroscopy"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_DomainsParallelChemistry"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersAMR"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersFlowPaths"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersGeneric"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersHyperTree"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersOpenTURNS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelDIY2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelFlowPaths"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelGeometry"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelImaging"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelMPI"] = "DONT_WANT"
            tc.variables[
                "VTK_MODULE_ENABLE_VTK_FiltersParallelStatistics"
            ] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersParallelVerdict"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersPoints"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersProgrammable"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersReebGraph"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersSMP"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersSelection"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersTopology"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_FiltersVerdict"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_GUISupportMFC"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_GeovisCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_GeovisGDAL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOADIOS2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOAMR"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOAsynchronous"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOCGNSReader"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOCONVERGECFD"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOChemistry"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOCityGML"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOEnSight"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOExodus"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOExport"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOExportGL2PS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOExportPDF"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOFFMPEG"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOFides"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOGDAL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOGeoJSON"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOGeometry"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOH5Rage"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOH5part"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOHDF"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOIOSS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOImport"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOInfovis"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOLAS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOLSDyna"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOLegacy"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOMINC"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOMPIImage"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOMotionFX"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOMovie"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOMySQL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IONetCDF"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOODBC"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOOMF"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOOggTheora"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOOpenVDB"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOPDAL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOPIO"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOPLY"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallel"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallelExodus"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallelLSDyna"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallelNetCDF"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallelXML"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOParallelXdmf3"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOPostgreSQL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOSQL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOSegY"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOTRUCHAS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOTecplotTable"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOVPIC"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOVeraOut"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOVideo"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOXdmf2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_IOXdmf3"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingFourier"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingHybrid"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingMorphological"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingOpenGL2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingSources"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ImagingStencil"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_InfovisBoost"] = "DONT_WANT"
            tc.variables[
                "VTK_MODULE_ENABLE_VTK_InfovisBoostGraphAlgorithms"
            ] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_InfovisCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_InfovisLayout"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ParallelCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ParallelDIY"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ParallelMPI"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_PythonInterpreter"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingExternal"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingFFMPEGOpenGL2"] = "DONT_WANT"
            tc.variables[
                "VTK_MODULE_ENABLE_VTK_RenderingFreeTypeFontConfig"
            ] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingImage"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingLICOpenGL2"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingLOD"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingLabel"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingMatplotlib"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingOpenVR"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingParallel"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingParallelLIC"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingRayTracing"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingSceneGraph"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingVR"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingVolumeAMR"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingVtkJS"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_TestingCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_TestingGenericBridge"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_TestingIOSQL"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_TestingRendering"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_UtilitiesBenchmarks"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_ViewsContext2D"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_WebCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_WebGLExporter"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_WrappingPythonCore"] = "DONT_WANT"
            tc.variables["VTK_MODULE_ENABLE_VTK_WrappingTools"] = "DONT_WANT"

        if self.options.minimal:
            tc.variables["VTK_Group_StandAlone"] = "OFF"
            tc.variables["VTK_Group_Rendering"] = "OFF"
        if self.options.ioxml:
            tc.variables["Module_vtkIOXML"] = "ON"
        if self.options.ioexport:
            tc.variables["Module_vtkIOExport"] = "ON"
        if self.options.ioxdmf3:
            tc.variables["Module_vtkIOXdmf3"] = "ON"
        if self.options.iolegacy:
            tc.variables["Module_vtkIOLegacy"] = "ON"
            # if tools.os_info.is_macos:
            # cmake.definitions["VTK_USE_SYSTEM_LIBXML2"] = "ON"
        if self.options.qt:
            tc.variables["VTK_GROUP_ENABLE_Qt"] = "YES"
            tc.variables["VTK_MODULE_ENABLE_VTK_GUISupportQt"] = "YES"
            tc.variables["VTK_MODULE_ENABLE_VTK_GUISupportQtQuick"] = "NO"
            tc.variables["VTK_MODULE_ENABLE_VTK_GUISupportQtSQL"] = "NO"
            tc.variables["VTK_MODULE_ENABLE_VTK_RenderingQt"] = "YES"
            tc.variables["VTK_MODULE_ENABLE_VTK_ViewsQt"] = "YES"
            tc.variables["VTK_QT_VERSION"] = "6"
            tc.variables["VTK_BUILD_QT_DESIGNER_PLUGIN"] = "OFF"
        if self.options.mpi:
            tc.variables["VTK_Group_MPI"] = "ON"
            tc.variables["Module_vtkIOParallelXML"] = "ON"
        if self.options.mpi_minimal:
            tc.variables["Module_vtkIOParallelXML"] = "ON"
            tc.variables["Module_vtkParallelMPI"] = "ON"

        if (
            self.settings.build_type == "Debug"
            and self.settings.compiler == "Visual Studio"
        ):
            tc.variables["CMAKE_DEBUG_POSTFIX"] = "_d"

        if self.settings.os == "Macos":
            self.env["DYLD_LIBRARY_PATH"] = os.path.join(self.build_folder, "lib")
            self.output.info("cmake build: %s" % self.build_folder)

        tc.variables["CMAKE_TOOLCHAIN_FILE"] = "conan_toolchain.cmake"
        tc.variables["CMAKE_INSTALL_PREFIX"] = str(
            Path(self.build_folder, "install")
        ).replace("\\", "/")

        tc.variables["CMAKE_CONFIGURATION_TYPES"] = "Debug;RelWithDebInfo;Release"

        return tc

    def generate(self):
        print("In generate")
        tc = self._get_tc()
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _configure_cmake(self):
        cmake = CMake(self)
        print(f"source path {str(PureWindowsPath(self.source_subfolder))}")
        cmake.configure(
            build_script_folder="vtk"
        )  # build_script_folder=str(PureWindowsPath(self.source_subfolder))
        return cmake

    def _do_build(self, cmake, build_type):
        # if self.settings.os == "Macos":
        # run_environment does not work here because it appends path just from
        # requirements, not from this package itself
        # https://docs.conan.io/en/latest/reference/build_helpers/run_environment.html#runenvironment
        #    lib_path = os.path.join(self.build_folder, "lib")
        #    self.run(
        #        f"DYLD_LIBRARY_PATH={lib_path} cmake --build build {cmake.build_config} -j"
        #    )
        cmake.build(build_type=build_type)
        cmake.install(build_type=build_type)

    def build(self):

        # Until we know exactly which vtk dlls are needed just build release
        # cmake_debug = self._configure_cmake()
        # self._do_build(cmake_debug, "Debug")

        cmake_release = self._configure_cmake()
        self._do_build(cmake_release, "Release")

    # From https://git.ircad.fr/conan/conan-vtk/blob/stable/8.2.0-r1/conanfile.py
    def cmake_fix_path(self, file_path, package_name):
        try:
            tools.replace_in_file(
                file_path,
                self.deps_cpp_info[package_name].rootpath.replace("\\", "/"),
                "${CONAN_" + package_name.upper() + "_ROOT}",
                strict=False,
            )
        except:
            self.output.info("Ignoring {0}...".format(package_name))

    def cmake_fix_macos_sdk_path(self, file_path):
        # Read in the file
        with open(file_path, "r") as file:
            file_data = file.read()

        if file_data:
            # Replace the target string
            file_data = re.sub(
                # Match sdk path
                r";/Applications/Xcode\.app/Contents/Developer/Platforms/MacOSX\.platform/Developer/SDKs/MacOSX\d\d\.\d\d\.sdk/usr/include",
                "",
                file_data,
                re.M,
            )

            # Write the file out again
            with open(file_path, "w") as file:
                file.write(file_data)

    # Package has no build type marking
    def package_id(self):
        del self.info.settings.build_type
        if self.settings.compiler == "Visual Studio":
            del self.info.settings.compiler.runtime

    def _pkg_bin(self, build_type):
        src_dir = f"{self.build_folder}/lib/{build_type}"
        dst_lib = f"lib/{build_type}"
        dst_bin = f"bin/{build_type}"
        self.copy("*.lib", src=src_dir, dst=dst_lib, keep_path=False)
        self.copy("*.dll", src=src_dir, dst=dst_bin, keep_path=False)
        self.copy("*.so", src=src_dir, dst=dst_lib, keep_path=False)
        self.copy("*.dylib", src=src_dir, dst=dst_lib, keep_path=False)
        self.copy("*.a", src=src_dir, dst=dst_lib, keep_path=False)
        if ((build_type == "Debug") or (build_type == "RelWithDebInfo")) and (
            self.settings.compiler == "Visual Studio"
        ):
            self.copy("*.pdb", src=src_dir, dst=dst_lib, keep_path=False)

    def package(self):
        for path, subdirs, names in os.walk(
            os.path.join(self.package_folder, "lib", "cmake")
        ):
            for name in names:
                if fnmatch(name, "*.cmake"):
                    cmake_file = os.path.join(path, name)

                    # if self.options.external_tiff:
                    # self.cmake_fix_path(cmake_file, "libtiff")
                    # if self.options.external_zlib:
                    # self.cmake_fix_path(cmake_file, "zlib")

                    if tools.os_info.is_macos:
                        self.cmake_fix_macos_sdk_path(cmake_file)
        # Debug
        # self._pkg_bin("Debug")
        # Release
        self._pkg_bin("Release")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        self.cpp_info.includedirs = [
            "include/vtk-%s" % self.short_version,
            "include/vtk-%s/vtknetcdf/include" % self.short_version,
            "include/vtk-%s/vtknetcdfcpp" % self.short_version,
        ]

        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
