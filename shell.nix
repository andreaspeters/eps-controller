with import <nixpkgs> {};

stdenv.mkDerivation {
name = "python-env";

buildInputs = [
    python311Full
    python311Packages.pip
    python311Packages.virtualenv
    python311Packages.tkinter
    lighttpd
];

SOURCE_DATE_EPOCH = 315532800;
PROJDIR = "/tmp/python-dev";
USER = builtins.getEnv "USER";
S_NETWORK="host";
S_VOLUME_RO="/home/andreas/.pypirc";

shellHook = ''
    echo "Using ${python311.name}"
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
    
    [ ! -d '$PROJDIR' ] && virtualenv $PROJDIR && echo "SETUP python-dev: DONE"
    source $PROJDIR/bin/activate
		pip install -r requirements.txt
    '';
}
