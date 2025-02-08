import curses
from datetime import datetime
import hashlib


def message_browser(stdscr, messages):
    curses.curs_set(0)
    stdscr.clear()

    selected = set()
    trash_bin = []
    index = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(
            0,
            0,
            "↑/↓ to navigate, Space to select, D to delete, U to undo, Q to quit",
            curses.A_BOLD,
        )

        for i, message in enumerate(messages):
            sender, receiver, timestamp, msg = message.split(",")
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime(
                "%Y-%m-%d"
            )
            formatted_msg = f"From {sender} to {receiver} on {timestamp}: {msg}"
            prefix = "[X] " if i in selected else "[ ] "
            if i == index:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(
                    i + 1, 0, prefix + formatted_msg[: width - 5]
                )  # Crop long messages
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(i + 1, 0, prefix + formatted_msg[: width - 5])

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and index > 0:
            index -= 1
        elif key == curses.KEY_DOWN and index < len(messages) - 1:
            index += 1
        elif key == ord(" "):
            if index in selected:
                selected.remove(index)
            else:
                selected.add(index)
        elif key == ord("d") and selected:
            confirm = confirm_delete(stdscr, selected, messages)
            if confirm:
                deleted = [(i, messages[i]) for i in selected]
                trash_bin.extend(deleted)
                messages = [msg for i, msg in enumerate(messages) if i not in selected]
                selected.clear()
                index = min(index, len(messages) - 1)
        elif key == ord("u") and trash_bin:
            last_deleted = trash_bin.pop()
            for i, msg in sorted(last_deleted, reverse=True):
                messages.insert(i, msg)
        elif key == ord("q"):
            break

    return messages, [msg for _, msg in trash_bin]


def confirm_delete(stdscr, selected, messages):
    """Ask for confirmation before deleting selected messages"""
    stdscr.clear()
    stdscr.addstr(
        0,
        0,
        "Are you sure you want to delete the following messages? (Y/N)",
        curses.A_BOLD,
    )

    y_offset = 2
    for i in selected:
        stdscr.addstr(y_offset, 0, f"- {messages[i]}")
        y_offset += 1

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in [ord("y"), ord("Y")]:
            return True
        elif key in [ord("n"), ord("N")]:
            return False


def hash_password(password):
    password_obj = password.encode("utf-8")
    return hashlib.sha256(password_obj).hexdigest()
