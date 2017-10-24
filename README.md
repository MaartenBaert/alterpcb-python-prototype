AlterPCB Python Prototype
=========================

AlterPCB is an open-source, cross-platform PCB design program. This is the Python prototype version. The 'real' (C++) version can be found here:

https://github.com/MaartenBaert/alterpcb

Getting started
---------------

This program is usable, but very slow and not user-friendly. Incorrect use can produce errors, I have no intention to fix this since this was only a prototype. **I do not offer any support for this. Please do not e-mail me questions, bug reports or feature requests, they will probably be ignored.**

A few example PCBs can be found in `pcb_biastee_maarten` and `pcb_chip1_testboard`.

You can start the program by running:

    ./alterpcb_editor.py <dir1> <dir2> ...

The directories are used to load AlterPCB libraries. AlterPCB does not make a distiction between footprint libraries and PCB documents like most other PCB tools do - it's all the same. So usually you want to load both the 'components' directory (which contains basic components like resistors) as well as your project directory. For example:

    ./alterpcb_editor.py components pcb_biastee_maarten

**All features are actived by hotkeys. Press F1 to see a list of all hotkeys and their function.**

The code has never been tested on any platform other than Linux. In theory it should be cross-platform, but some steps (e.g. Gerber export) require command-line tools like `zip`, which generally aren't available on non-Unix platforms.

License
-------

GNU GPL v3 - read 'COPYING' for more info.
