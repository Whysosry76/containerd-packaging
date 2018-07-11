BuildRoot: /root/.tmp/rpmrebuild.95/work/root
AutoProv: no
%undefine __find_provides
AutoReq: no
%undefine __find_requires

%undefine __check_files
%undefine __find_prereq
%undefine __find_conflicts
%undefine __find_obsoletes

# Build policy set to nothing
%define __spec_install_post %{nil}
# For rmp-4.1
%define __missing_doc_files_terminate_build 0

%bcond_without ctr
%bcond_with debug

%if %{with debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package %{nil}
%endif

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -x %{?**};
%endif

%define SHA256SUM0 08f057ece7e518b14cce2e9737228a5a899a7b58b78248a03e02f4a6c079eeaf
%global import_path github.com/containerd/containerd
%global gopath %{getenv:GOPATH}

Name: containerd
Version: %{getenv:RPM_VERSION}
Release: %{getenv:RPM_RELEASE_VERSION}%{dist}
Summary: An industry-standard container runtime
License: ASL 2.0
URL: https://containerd.io
Source0: containerd
Source1: containerd.service
Source2: containerd.toml
BuildRequires: systemd
BuildRequires: btrfs-progs-devel
%{?systemd_requires}
# https://github.com/containerd/containerd/issues/1508#issuecomment-335566293
Requires: runc >= 1.0.0

%description
containerd is an industry-standard container runtime with an emphasis on
simplicity, robustness and portability. It is available as a daemon for Linux
and Windows, which can manage the complete container lifecycle of its host
system: image transfer and storage, container execution and supervision,
low-level storage and network attachments, etc.


%prep
rm -rf %{_topdir}/BUILD/
# Copy over our source code from our gopath to our source directory
cp -rf /go/src/%{import_path} %{_topdir}/SOURCES/containerd
# symlink the go source path to our build directory
ln -s /go/src/%{import_path} %{_topdir}/BUILD
cd %{_topdir}/BUILD/


%build
cd %{_topdir}/BUILD
# needed for man pages
go get -u github.com/cpuguy83/go-md2man
make man

export LDFLAGS="-X %{import_path}/version.Package=%{import_path} -X %{import_path}/version.Version=%{getenv:VERSION} -X %{import_path}/version.Revision=%{getenv:REF}"
%gobuild -o bin/containerd %{import_path}/cmd/containerd
%gobuild -o bin/containerd-shim %{import_path}/cmd/containerd-shim
%gobuild -o bin/ctr %{import_path}/cmd/ctr


%install
cd %{_topdir}/BUILD
install -D -m 0755 bin/containerd %{buildroot}%{_bindir}/containerd
install -D -m 0755 bin/containerd-shim %{buildroot}%{_bindir}/containerd-shim
install -D -m 0755 bin/ctr %{buildroot}%{_bindir}/ctr
install -D -m 0644 %{S:1} %{buildroot}%{_unitdir}/containerd.service
install -D -m 0644 %{S:2} %{buildroot}%{_sysconfdir}/containerd/config.toml

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 man/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1
install -d %{buildroot}%{_mandir}/man5
install -p -m 644 man/*.5 $RPM_BUILD_ROOT/%{_mandir}/man5

%post
%systemd_post containerd.service


%preun
%systemd_preun containerd.service


%postun
%systemd_postun_with_restart containerd.service


%files
%license LICENSE
%doc README.md
%{_bindir}/containerd
%{_bindir}/containerd-shim
%{?with_ctr:%{_bindir}/ctr}
%{_unitdir}/containerd.service
%{_sysconfdir}/containerd
/%{_mandir}/man1/*
/%{_mandir}/man5/*
%config(noreplace) %{_sysconfdir}/containerd/config.toml


%changelog
* Tue May 01 2018 Jose Bigio <jose.bigio@docker.com> - 1.1.0
- Initial Package