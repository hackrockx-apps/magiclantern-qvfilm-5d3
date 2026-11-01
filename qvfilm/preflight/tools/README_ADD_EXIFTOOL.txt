ADD EXIFTOOL FOR WINDOWS (64-BIT)
1) Download the official Windows ZIP from https://exiftool.org/ and extract it.
2) Rename exiftool(-k).exe to exiftool.exe.
3) Move BOTH exiftool.exe AND its companion exiftool_files FOLDER into THIS tools/ directory.
4) Expected layout:
   preflight.py
   QVFILM_START_WIN10.cmd
   tools/exiftool.exe
   tools/exiftool_files/...
5) In a CMD opened in the program directory run: tools\exiftool.exe -ver
   Expected: prints an ExifTool version number.
6) If your antivirus quarantined the EXE, do not bypass protection blindly;
   get it only from the official ExifTool website and verify the publisher/source.
No executable is bundled in the QVFilm archive. Never install anything on the camera.
