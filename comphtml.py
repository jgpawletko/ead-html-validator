from bs4 import BeautifulSoup, NavigableString, Tag
from resultset import ResultSet
import logging
import os.path
import re
import util


class CompHTML:
    def __init__(self, c, cid):
        self.c = c
        self.id = cid
        self.cid = cid
        self.level = self._level()

    def __str__(self):
        # return str(self.c)
        return self.c.prettify()

    def accessrestrict(self):
        return self.formatted_note_text("accessrestrict")

    def accessrestrict_heading(self):
        return self.formatted_note_heading("accessrestrict")

    def accruals(self):
        return self.formatted_note_text("accruals")

    def accruals_heading(self):
        return self.formatted_note_heading("accruals")

    def acqinfo(self):
        return self.formatted_note_text("acqinfo")

    def acqinfo_heading(self):
        return self.formatted_note_heading("acqinfo")

    def altformavail(self):
        return self.formatted_note_text("altformavail")

    def altformavail_heading(self):
        return self.formatted_note_heading("altformavail")

    def appraisal(self):
        return self.formatted_note_text("appraisal")

    def appraisal_heading(self):
        return self.formatted_note_heading("appraisal")

    def arrangement(self):
        return self.formatted_note_text("arrangement")

    def arrangement_heading(self):
        return self.formatted_note_heading("arrangement")

    def bioghist(self):
        return self.formatted_note_text("bioghist")

    def bioghist_heading(self):
        return self.formatted_note_heading("bioghist")

    def component(self):
        regex = re.compile(r"^level")
        first_c = self.c.find("div", class_=regex)
        if first_c is None:
            return []
        comps = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            if c.has_attr("id"):
                cid = c["id"]
            else:
                cid = c.find(re.compile(r"^h\d$"), recursive=False)["id"]
            comps.append(CompHTML(c, cid))
        return comps

    def component_id_level(self):
        regex = re.compile(r"^level")
        first_c = self.c.find("div", class_=regex)
        if first_c is None:
            return []
        id_level = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            if c.has_attr("id"):
                cid = c["id"]
            else:
                cid = c.find(re.compile(r"^h\d$"), recursive=False)["id"]
            id_level.append((cid, re.split(r"[- ]", c["class"])[1]))
        return id_level

    def contents(self):
        return [text for text in self.c.stripped_strings]

    def control_group(self, field):
        ctrl_access = self.md_group("controlaccess")
        if not ctrl_access:
            return None
        ctrl_group = ctrl_access.find(
            "div", class_=f"controlaccess-{field}-group"
        )
        if ctrl_group is None:
            return None
        # return ctrl_group.div.get_text(strip=True)
        if ctrl_group.div:
            return CompHTML.find_all(ctrl_group, "div")
        else:
            return None

    def corpname(self):
        return self.control_group("corpname")

    def creator(self):
        origin = self.md_group("origination")
        if origin is None:
            return None
        # return [
        #     name.get_text()
        #     for name in origin.find_all("div", class_=re.compile(r"name$"))
        # ]
        return CompHTML.find_all(origin, "div", class_=re.compile(r"name$"))

    def custodhist(self):
        return self.formatted_note_text("custodhist")

    def custodhist_heading(self):
        return self.formatted_note_heading("custodhist")

    def _dao(self, dao_type=""):
        return self.c.find_all(
            "div",
            class_=re.compile(rf"^md-group dao-item {dao_type}"),
            recursive=False,
        )

    def dao(self, html_dir, roles):
        daos = self._dao()
        if not daos:
            return None

        dao_set = ResultSet(value_type=dict)
        for i, dao in enumerate(daos):
            dao_data = {}

            dao_data["role"] = [dao["class"].split()[2]]

            get_text = dao_data["role"][0] != "external-link"
            desc = CompHTML.find_all(
                dao, attrs={"data-ead-element": "daodesc"}, get_text=get_text
            )
            if desc:
                dao_data["desc"] = desc.values()

            links = []
            for a in dao.find_all(
                "a", class_=re.compile(r"^dao-link"), href=True
            ):
                link = a["href"]
                if link.startswith("/"):
                    link = self.permalink(link, html_dir) or link
                links.append(link)
            if links:
                dao_data["link"] = links

            dao_set.add(dao.name, {f"dao {i + 1}.": dao_data}, dao.sourceline)

        return dao_set if dao_set else None

    def dao_desc(self):
        daos = self._dao()
        if daos is None:
            return None
        descriptions = ResultSet()
        for dao in daos:
            for desc in dao.find_all(class_=re.compile(r"dao-description")):
                text = [
                    string
                    for string in desc.strings
                    if not re.match("https?://", string)
                ]
                # descriptions.add("".join(text).strip())
                text = util.clean_text("".join(text))
                descriptions.add(desc.name, text, desc.sourceline)
        # return list(descriptions) if descriptions else None
        return descriptions if descriptions else None

    # def dao_desc(self):
    #     return self.dao_title()

    def dao_link(self):
        # daos = self._dao("external-link")
        daos = self._dao()
        if daos is None:
            return None
        links = ResultSet()
        for dao in daos:
            # links.update({a["href"] for a in dao.find_all("a")})
            link = CompHTML.find_all(dao, "a", attrib="href")
            if link:
                links.append(link)
        # return sorted(list(links)) if links else None
        return links if links else None

    def dao_title(self):
        daos = self._dao()
        if daos is None:
            return None
        logging.debug(daos)
        titles = ResultSet()
        for dao in daos:
            for title in dao.find_all(class_=re.compile(r"item-title")):
                # text = [
                #     child
                #     for child in title.contents
                #     if isinstance(child, NavigableString)
                # ]
                text = [
                    string
                    for string in title.strings
                    if not re.match("https?://", string)
                ]
                # titles.add("".join(text).strip().rsplit(":", 1)[0])
                # titles.add(util.strip_date("".join(text).strip()))
                # titles.add("".join(text).strip())
                text = util.clean_text("".join(text))
                titles.add(title.name, text, title.sourceline)
        # return list(titles) if titles else None
        return titles if titles else None

    def dimensions(self):
        return self.physdesc("dimensions")

    def extent(self):
        return self.physdesc("extent")

    def famname(self):
        return self.control_group("famname")

    def fileplan(self):
        return self.formatted_note_text("fileplan")

    def fileplan_heading(self):
        return self.formatted_note_heading("fileplan")

    @staticmethod
    def find_all(
        root,
        *args,
        attrib=None,
        get_text=True,
        join_text=False,
        join_uniq=True,
        sep="",
        join_sep=" ",
        **kwargs,
    ):
        nodes = root.find_all(*args, **kwargs)
        if not nodes:
            return None

        total_text = ""
        find_expr = util.create_args_str(*args, **kwargs)
        result = ResultSet(xpath=find_expr)
        for node in nodes:
            if attrib:
                text = node[attrib]
            elif get_text:
                text = node.get_text(sep)
            else:
                text = node.contents[0]
            text = util.clean_text(text)
            result.add(node.name, text, node.sourceline)

        if join_text:
            result = result.join(sep=join_sep, uniq=join_uniq)

        return result

    def formatted_note(self, field):
        return self.c.find_all(
            "div", class_=f"md-group formattednote {field}", recursive=False
        )

    def formatted_note_heading(self, field):
        notes = self.formatted_note(field)
        if not notes:
            return None
        heading = ResultSet()
        for note in notes:
            hdr = CompHTML.find_all(
                note,
                re.compile(r"^h\d$"),
                class_="formattednote-header",
                sep="",
            )
            if hdr:
                heading.append(hdr)
        return heading if heading else None

    def formatted_note_text(self, field, p=True, **kwargs):
        notes = self.formatted_note(field)
        if not notes:
            return None
        text = ResultSet()
        for note in notes:
            # search_root = note if note.p else note.div
            values = CompHTML.find_all(
                note, re.compile("^(div|p)$"), recursive=False, **kwargs
            )
            if values:
                text.append(values)
        return text if text else None

    def function(self):
        return self.control_group("function")

    def genreform(self):
        return self.control_group("genreform")

    def geogname(self):
        return self.control_group("geogname")

    def _id(self):
        return self.id

    def langcode(self):
        pass

    def language(self):
        lang = self.md_group("langmaterial")
        if lang is None:
            return None
        # return lang.span.get_text()
        for tag in ["span", "div"]:
            lang_child = getattr(lang, tag)
            if lang_child is not None:
                return CompHTML.resultset(lang_child)
        return None

    def _level(self):
        if (
            self.c.name == "div"
            and self.c.has_attr("class")
            and self.c["class"].startswith("level")
        ):
            lvl = re.split("[- ]", self.c["class"])[1]
        else:
            lvl = None
        return lvl

    def md_group(self, group_name):
        return self.c.find(
            "div", class_=f"md-group {group_name}", recursive=False
        )

    def name(self):
        pass

    def occupation(self):
        return self.control_group("occupation")

    def odd(self):
        return self.formatted_note_text("odd", p=False, sep=" ")

    def odd_heading(self):
        return self.formatted_note_heading("odd")

    def originalsloc(self):
        return self.formatted_note_text("originalsloc")

    def originalsloc_heading(self):
        return self.formatted_note_heading("originalsloc")

    def otherfindaid(self):
        return self.formatted_note_text("otherfindaid")

    def otherfindaid_heading(self):
        return self.formatted_note_heading("otherfindaid")

    def permalink(self, link, html_dir):
        dirparts = link.strip(os.sep).split(os.sep)
        partner = dirparts[0]
        eadid = dirparts[1]
        logging.trace(f"parter: {partner}")
        logging.trace(f"eadid: {eadid}")
        logging.trace(f"dirparts: {dirparts[2:]}")

        html_file = os.path.join(html_dir, *dirparts[2:], "index.html")
        logging.debug("permalink html file: {html_file}")
        if not os.path.isfile(html_file):
            return None
        soup = BeautifulSoup(open(html_file), "html.parser")
        link = soup.find(class_="dl-permalink")
        if not link:
            return None
        url = link.contents[1].strip()
        logging.debug(f"permalink for {link} is {url}")
        return url

    def persname(self):
        pass

    def physdesc(self, field):
        # phys_desc = self.c.find("div", class_=re.compile("physdesc"))
        phys_desc = self.formatted_note("physdesc")
        if not phys_desc:
            return None
        header = phys_desc[0].find(re.compile("h\d"), class_=re.compile(field))
        if not header:
            return None
        sib = header.find_next_sibling("div")
        return CompHTML.resultset(sib) if sib else None

    def physfacet(self):
        return self.physdesc("physfacet")

    def physloc(self):
        loc = self.formatted_note("physloc")
        if not loc:
            return None
        # return "".join([span.get_text() for span in loc.find_all("span")])
        return CompHTML.find_all(loc[0], "span", join_text=True, join_sep="")

    def physloc_heading(self):
        return self.formatted_note_heading("physloc")

    def phystech(self):
        return self.formatted_note_text("phystech")

    def phystech_heading(self):
        return self.formatted_note_heading("phystech")

    def prefercite(self):
        return self.formatted_note_text("prefercite")

    def prefercite_heading(self):
        return self.formatted_note_heading("prefercite")

    def processinfo(self):
        return self.formatted_note_text("processinfo")

    def processinfo_heading(self):
        return self.formatted_note_heading("processinfo")

    def relatedmaterial(self):
        return self.formatted_note_text("relatedmaterial")

    def relatedmaterial_heading(self):
        return self.formatted_note_heading("relatedmaterial")

    @staticmethod
    def resultset(node, xpath=None, sep=""):
        return ResultSet(xpath=xpath).add(
            node.name, util.clean_text(node.get_text(sep)), node.sourceline
        )

    def separatedmaterial(self):
        return self.formatted_note_text("separatedmaterial")

    def separatedmaterial_heading(self):
        return self.formatted_note_heading("separatedmaterial")

    def scopecontent(self):
        return self.formatted_note_text("scopecontent")

    def scopecontent_heading(self):
        return self.formatted_note_heading("scopecontent")

    def sub_components(self):
        pass

    def subject(self):
        return self.control_group("subject")

    def title(self):
        # return self.c.find(re.compile("h\d"), class_="unittitle").text
        text = ""
        unit_title = self.c.find(
            re.compile("h\d"), class_="unittitle", recursive=False
        )
        for child in unit_title:
            if not (
                isinstance(child, Tag)
                and child.get("class") in ["dates", "delim"]
            ):
                text += child.get_text()
        return ResultSet().add(
            unit_title.name, util.clean_text(text), unit_title.sourceline
        )

    def unitdate(self):
        # date = self.c.find(re.compile(r"^h\d$"), class_="unittitle").find(
        #     "span", class_="dates"
        # )
        # return date.get_text()
        unit_title = self.c.find(
            re.compile(r"^h\d$"), class_="unittitle", recursive=False
        )
        if not unit_title:
            return None
        return CompHTML.find_all(unit_title, "span", class_="dates")

    def unitid(self):
        odd = self.formatted_note("odd")
        if odd is None:
            return None
        # return odd.find("span", class_="ead-num").get_text()
        return CompHTML.find_all(odd, "span", class_="ead-num")

    def unittitle(self):
        return self.title()

    def userestrict(self):
        return self.formatted_note_text("userestrict")

    def userestrict_heading(self):
        return self.formatted_note_heading("userestrict")
