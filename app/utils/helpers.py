from flask import flash


def success(message):
    flash(message, "success")


def error(message):
    flash(message, "danger")


def warning(message):
    flash(message, "warning")


def info(message):
    flash(message, "info")