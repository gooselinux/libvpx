Name:			libvpx
Summary:		VP8 Video Codec SDK
Version:		0.9.0
Release:		7%{?dist}
License:		BSD
Group:			System Environment/Libraries
Source0:		http://webm.googlecode.com/files/%{name}-%{version}.tar.bz2
Source1:		libvpx.pc
# Thanks to debian.
Source2:		libvpx.ver
Patch0:			libvpx-0.9.0-no-explicit-dep-on-static-lib.patch
# Hackish fix for bz 599147
# See: https://groups.google.com/a/webmproject.org/group/codec-devel/browse_frm/thread/ff90bd82d0369b96/79d4c40ea78db91b?tvc=1&q=timothy#79d4c40ea78db91b
Patch1:			0001-Test-commit-for-a-version-of-the-SPLITMV-bounds-patc.patch
Patch2:			libvpx-0.9.0-gas.patch
URL:			http://www.webmproject.org/tools/vp8-sdk/
BuildRequires:		doxygen, php-cli

%description
libvpx provides the VP8 SDK, which allows you to integrate your applications 
with the VP8 video codec, a high quality, royalty free, open source codec 
deployed on millions of computers and devices worldwide. 

%package devel
Summary:		Development files for libvpx
Group:			Development/Libraries
Requires:		%{name} = %{version}-%{release}

%description devel
Development libraries and headers for developing software against 
libvpx.

%package utils
Summary:		VP8 utilities and tools
Group:			Development/Tools
Requires:		%{name} = %{version}-%{release}

%description utils
A selection of utilities and tools for VP8, including a sample encoder
and decoder.

%prep
%setup -q
%patch0 -p1 -b .no-static-lib
%patch1 -p1 -b .bz599147
%patch2 -p1 -b .gas

%build
%ifarch %{ix86}
%global vpxtarget x86-linux-gcc
%else
%ifarch	x86_64
%global	vpxtarget x86_64-linux-gcc
%else
%global vpxtarget generic-gnu
%endif
%endif

./configure --target=%{vpxtarget} --enable-pic --disable-install-srcs

# Hack our optflags in.
sed -i "s|\"vpx_config.h\"|\"vpx_config.h\" %{optflags} -fPIC|g" libs-%{vpxtarget}.mk
sed -i "s|\"vpx_config.h\"|\"vpx_config.h\" %{optflags} -fPIC|g" examples-%{vpxtarget}.mk
sed -i "s|\"vpx_config.h\"|\"vpx_config.h\" %{optflags} -fPIC|g" docs-%{vpxtarget}.mk

make %{?_smp_mflags} verbose=true target=libs

# Really? You couldn't make this a shared library? Ugh.
# Oh well, I'll do it for you.
mkdir tmp
cd tmp
ar x ../libvpx_g.a
cd ..
gcc -fPIC -shared -pthread -lm -Wl,--no-undefined -Wl,-soname,libvpx.so.0 -Wl,--version-script,%{SOURCE2} -Wl,-z,noexecstack -o libvpx.so.0.0.0 tmp/*.o 
rm -rf tmp

# Temporarily dance the static libs out of the way
mv libvpx.a libNOTvpx.a
mv libvpx_g.a libNOTvpx_g.a

# We need to do this so the examples can link against it.
ln -sf libvpx.so.0.0.0 libvpx.so

make %{?_smp_mflags} verbose=true target=examples
make %{?_smp_mflags} verbose=true target=docs

# Put them back so the install doesn't fail
mv libNOTvpx.a libvpx.a
mv libNOTvpx_g.a libvpx_g.a

%install
make DIST_DIR=%{buildroot}%{_prefix} install

# Install the pkg-config file
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
install -m0644 %{SOURCE1} %{buildroot}%{_libdir}/pkgconfig/
# Fill in the variables
sed -i "s|@PREFIX@|%{_prefix}|g" %{buildroot}%{_libdir}/pkgconfig/libvpx.pc
sed -i "s|@LIBDIR@|%{_libdir}|g" %{buildroot}%{_libdir}/pkgconfig/libvpx.pc
sed -i "s|@INCLUDEDIR@|%{_includedir}|g" %{buildroot}%{_libdir}/pkgconfig/libvpx.pc

# Simpler to label the dir as %doc.
mv %{buildroot}/usr/docs doc/

mkdir -p %{buildroot}%{_includedir}/vpx/
install -p libvpx.so.0.0.0 %{buildroot}%{_libdir}
pushd %{buildroot}%{_libdir}
ln -sf libvpx.so.0.0.0 libvpx.so
ln -sf libvpx.so.0.0.0 libvpx.so.0
ln -sf libvpx.so.0.0.0 libvpx.so.0.0
popd
pushd %{buildroot}
# Stuff we don't need.
rm -rf usr/build/ usr/md5sums.txt usr/lib*/*.a usr/CHANGELOG usr/README
# Rename a few examples
mv usr/bin/simple_decoder usr/bin/vp8_simple_decoder
mv usr/bin/simple_encoder usr/bin/vp8_simple_encoder
mv usr/bin/twopass_encoder usr/bin/vp8_twopass_encoder
# Move the headers into the subdir
mv usr/include/*.h usr/include/vpx/
# Fix the binary permissions
chmod 755 usr/bin/*
popd

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%doc AUTHORS CHANGELOG LICENSE README
%{_libdir}/libvpx.so.*

%files devel
%defattr(-,root,root,-)
# These are SDK docs, not really useful to an end-user.
%doc doc/
%{_includedir}/vpx/
%{_libdir}/pkgconfig/libvpx.pc
%{_libdir}/libvpx.so

%files utils
%defattr(-,root,root,-)
%{_bindir}/*

%changelog
* Wed Jun 27 2010 Benjamin Otte <otte@redhat.com> 0.9.0-7
- Import 0.9.0-6 package from Fedora
- Add patch porting yasm syntax to gas
Related: rhbz#603113
