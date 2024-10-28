{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.iana-etc
    pkgs.file
    pkgs.openssl
    pkgs.postgresql
  ];
}
