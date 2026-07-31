from functools import wraps

from flask import flash, redirect, url_for

from flask_login import current_user


def admin_required(func):

    @wraps(func)

    def wrapper(*args, **kwargs):

        if current_user.role != "Admin":

            flash(
                "Access Denied!",
                "danger"
            )

            return redirect(
                url_for("auth.dashboard")
            )

        return func(*args, **kwargs)

    return wrapper