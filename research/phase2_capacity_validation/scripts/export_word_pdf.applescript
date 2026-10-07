on run argv
    set sourcePath to item 1 of argv
    set destPath to item 2 of argv
    tell application "Microsoft Word"
        activate
        open (POSIX file sourcePath)
        set d to active document
        save as d file name destPath file format format PDF
        close d saving no
    end tell
end run
