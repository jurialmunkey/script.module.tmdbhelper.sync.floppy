LIST_ROUTES = {
    name: {
        'module_name': 'tmdbhelper_sync_floppy.directories.lists',
        'import_attr': class_name,
    } for name, class_name in (
        ('floppy_directory', 'ListFloppyDirectory'),
        ('floppy_lists', 'ListFloppyLists'),
        ('floppy_userlist', 'ListFloppyUserList'),
        ('floppy_watchlist', 'ListFloppyWatchlist'),
        ('floppy_collection', 'ListFloppyCollection'),
        ('floppy_watched', 'ListFloppyWatched'),
        ('floppy_progress', 'ListFloppyProgress'),
    )
}
