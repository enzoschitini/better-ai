DOCUMENTS = [
    "txt",
    "pdf",
    "doc",
    "docx",
    "odt",
    "rtf",
    "md",
    "csv",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
]

IMAGES = [
    "jpg",
    "jpeg",
    "png",
    "gif",
    "bmp",
    "webp",
    "tiff",
    "svg",
]

AUDIOS = [
    "mp3",
    "wav",
    "ogg",
    "aac",
    "flac",
    "m4a",
]

VIDEOS = [
    "mp4",
    "avi",
    "mov",
    "mkv",
    "webm",
    "flv",
    "wmv",
]

ALLOWED_EXTENSIONS = DOCUMENTS + IMAGES + AUDIOS + VIDEOS

MIMETYPES = {
    "documents": [
        "text/plain",                    # txt
        "application/pdf",              # pdf
        "application/msword",           # doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.oasis.opendocument.text",  # odt
        "application/rtf",              # rtf
        "text/markdown",                # md
        "text/csv",                     # csv
        "application/vnd.ms-excel",     # xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-powerpoint",  # ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
    ],

    "images": [
        "image/jpeg",   # jpg, jpeg
        "image/png",    # png
        "image/gif",    # gif
        "image/bmp",    # bmp
        "image/webp",   # webp
        "image/tiff",   # tiff
        "image/svg+xml" # svg
    ],

    "audios": [
        "audio/mpeg",   # mp3
        "audio/wav",    # wav
        "audio/ogg",    # ogg
        "audio/aac",    # aac
        "audio/flac",   # flac
        "audio/mp4",    # m4a
        "audio/x-m4a",  # common alternative
    ],

    "videos": [
        "video/mp4",        # mp4
        "video/x-msvideo",  # avi
        "video/quicktime",  # mov
        "video/x-matroska", # mkv
        "video/webm",       # webm
        "video/x-flv",      # flv
        "video/x-ms-wmv",   # wmv
    ]
}

ALL_MIMETYPES = sum(MIMETYPES.values(), [])



