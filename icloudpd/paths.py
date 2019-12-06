"""Path functions"""
import os


def local_download_path(media, size, download_dir):
    """Returns the full download path, including size"""
    filename = filename_with_size(media, size)
    download_path = os.path.join(download_dir, filename)
    return download_path


def filename_with_size(media, size):
    """Returns the filename with size, e.g. IMG1234.jpg, IMG1234-small.jpg"""
    # Strip any non-ascii characters.
    filename = media.filename.encode("utf-8").decode("ascii", "ignore")
    if size == 'original':
        return filename
    return ("-%s." % size).join(filename.rsplit(".", 1))


def local_download_path_lp(media, lp_size, download_dir):
    """
    Retruns the full download path to a live photos video path including size
    e.g.: img1234.mov, img1234-small.mov, etc.
    """
    if "Video" not in lp_size:
        raise Exception("ERROR: live photo size does not contain 'Video'")

    if lp_size in media.versions:
        version = media.versions[lp_size]
        filename = version["filename"]
        if lp_size != "originalVideo":
            size = lp_size.rstrip("Video")
            # Add size to filename if not original
            filename = ("-%s." % size).join(filename.rsplit(".", 1))
        lp_download_path = os.path.join(download_dir, filename)
        return lp_download_path

    else:
        raise Exception("No size {} found for {}".format(lp_size, media.id))
