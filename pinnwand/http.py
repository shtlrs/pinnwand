import json
import logging

from typing import List

from datetime import timedelta

import tornado.web

import tornado_sqlalchemy

from pinnwand import database
from pinnwand import utility


log = logging.getLogger(__name__)


class Base(tornado.web.RequestHandler, tornado_sqlalchemy.SessionMixin):
    pass


class PasteForm(Base):
    """The index page shows the new paste page with a list of all available
       lexers from Pygments."""

    async def get(self, lexer: str = "") -> None:
        """Render the new paste form, optionally have a lexer preselected from
           the URL."""

        lexers = utility.list_languages()

        # Make sure a valid lexer is given
        if lexer not in lexers:
            raise tornado.web.HTTPError(404)

        await self.render(
            "new.html", lexer=lexer, lexers=lexers, pagetitle="new"
        )


class About(Base):
    async def get(self) -> None:
        self.render("about.html", pagetitle="about")


class CreatePaste(Base):
    """..."""

    async def post(self) -> None:
        lexer = self.get_body_argument("lexer")
        raw = self.get_body_argument("code")
        expiry = self.get_body_argument("expiry")

        if lexer not in utility.list_languages():
            log.info("Paste.post: a paste was submitted with an invalid lexer")
            raise tornado.web.HTTPError(400)

        if expiry not in utility.expiries:
            log.info("Paste.post: a paste was submitted with an invalid expiry")
            raise tornado.web.HTTPError(400)

        paste = database.Paste(
            raw,
            lexer,
            expiry
        )

        with self.make_session() as session:
            session.add(paste)
            session.commit()

        # The removal cookie is set for the specific path of the paste it is
        # related to
        self.set_cookie(
            "removal", str(paste.removal_id), path=f"/show/{paste.paste_id}"
        )

        # Send the client to the paste
        self.redirect(f"/show/{paste.paste_id}")

    def check_xsrf_cookie(self) -> bool:
        """The CSRF token check is disabled. While it would be better if it
           was on the impact is both small (someone could make a paste in
           a users name which could allow pinnwand to be used as a vector for
           exfiltration from other XSS) and some command line utilities
           POST directly to this endpoint without using the JSON endpoint."""
        return True


class ShowPaste(Base):
    def get(self, paste_id: str) -> None:
        with self.make_session() as session:
            paste = (
                session.query(database.Paste)
                .filter(database.Paste.paste_id == paste_id)
                .first()
            )

        if not paste:
            self.set_status(404)
            self.render("404.html")
            return

        can_delete = self.get_cookie("removal") == str(paste.removal_id)

        self.render(
            "show.html", paste=paste, pagetitle="show", can_delete=can_delete
        )


class RawPaste(Base):
    async def get(self, paste_id: str) -> None:
        with self.make_session() as session:
            paste = (
                session.query(database.Paste)
                .filter(database.Paste.paste_id == paste_id)
                .first()
            )

        if not paste:
            self.set_status(404)
            self.render("404.html")
            return

        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write(paste.raw)


class RemovePaste(Base):
    """Remove a paste."""

    async def get(self, removal_id: str) -> None:
        """Look up if the user visiting this page has the removal id for a
           certain paste. If they do they're authorized to remove the paste."""

        # XXX maybe use one and catch error
        with self.make_session() as session:
            paste = (
                session.query(database.Paste)
                .filter(database.Paste.removal_id == removal_id)
                .first()
            )

            if not paste:
                log.info("RemovePaste.get: someone visited with invalid id")
                self.set_status(404)
                self.render("404.html")
                return

            session.delete(paste)
            session.commit()

        self.redirect("/")


class APIShow(Base):
    def get(self, paste_id: str) -> None:
        with self.make_session() as session:
            paste = (
                session.query(database.Paste)
                .filter(database.Paste.paste_id == paste_id)
                .first()
            )

        if not paste:
            self.set_status(404)
            return

        self.write(
            {
                "paste_id": paste.paste_id,
                "raw": paste.raw,
                "fmt": paste.fmt,
                "lexer": paste.lexer,
                "expiry": paste.exp_date.isoformat(),
            }
        )


class APINew(Base):
    async def post(self) -> None:
        lexer = self.get_body_argument("lexer")
        raw = self.get_body_argument("code")
        expiry = self.get_body_argument("expiry")

        if lexer not in utility.list_languages():
            log.info("APINew.post: a paste was submitted with an invalid lexer")
            raise tornado.web.HTTPError(400)

        if expiry not in utility.expiries:
            log.info("APINew.post: a paste was submitted with an invalid expiry")
            raise tornado.web.HTTPError(400)

        paste = database.Paste(
            raw,
            lexer,
            expiry
        )

        with self.make_session() as session:
            session.add(paste)
            session.commit()

        self.write({"paste_id": paste.paste_id, "removal_id": paste.removal_id})


class APIRemove(Base):
    async def post(self) -> None:
        with self.make_session() as session:
            paste = (
                session.query(database.Paste)
                .filter(
                    database.Paste.removal_id
                    == self.get_body_argument("removal_id")
                )
                .first()
            )

            if not paste:
                self.set_status(400)
                return

            session.delete(paste)
            session.commit()

        # XXX this is set this way because tornado tries to protect us
        # XXX by not allowing lists to be returned, looking at this code
        # XXX it really shouldn't be a list but we have to keep it for
        # XXX backwards compatibility
        self.set_header("Content-Type", "application/json")
        self.write(
            json.dumps([{"paste_id": paste.paste_id, "status": "removed"}])
        )


application = tornado.web.Application([
    (r"/+<lexer>", PasteForm),
    (r"/+<lexer>", CreatePaste),
    (r"/show/<pasteid>", ShowPaste),
    (r"/raw/<pasteid>", RawPaste),
])
