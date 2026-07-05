def progress_bar(current, total, length=30):
    percent = current / total
    bar = '█' * int(percent * length) + '-' * (length - int(percent * length))
    return f"[{bar}] {percent*100:.1f}%"