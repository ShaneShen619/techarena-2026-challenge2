on run argv
    set inputPath to item 1 of argv
    set outputPath to item 2 of argv
    tell application "Microsoft Word"
        activate
        open (POSIX file inputPath)
        set openedDoc to active document
        save as openedDoc file name (POSIX file outputPath) file format format PDF
        close openedDoc saving no
    end tell
end run
