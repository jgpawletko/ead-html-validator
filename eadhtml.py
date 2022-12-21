from bs4 import BeautifulSoup
from lxml import etree as ET
from resultset import ResultSet
from string import punctuation as punc
from subprocess import PIPE
import comphtml
import logging
import pycountry
import re
import shutil
import util


class ComponentNotFoundError(Exception):
    pass


class EADHTML:
    def __init__(self, html_file):
        logging.debug(f"html_file={html_file}")
        # self.soup = BeautifulSoup(open(html_file), "html.parser")
        self.soup = BeautifulSoup(
            open(html_file), "html.parser", multi_valued_attributes=None
        )
        self.dom = ET.HTML(str(self.soup))
        self.html_file = html_file

    def author(self):
        return self.soup.find("div", class_="md-group author").div.get_text()

    def abstract(self):
        return self.formatted_note("abstract")

    def accessrestrict(self):
        return self.formatted_note("accessrestrict")

    def accruals(self):
        return self.formatted_note("accruals")

    def acqinfo(self):
        return self.formatted_note("acqinfo")

    def altformavail(self):
        return self.formatted_note("altformavail")

    def appraisal(self):
        return self.formatted_note("appraisal")

    def arrangement(self):
        return self.formatted_note("arrangement")

    def bibliography(self):
        return self.formatted_note("bibliography")

    def bioghist(self):
        return self.formatted_note("bioghist")

    def chronlist(self):
        items = ResultSet(value_type=dict)
        clist = self.soup.find("span", class_="ead-chronlist")
        if not clist:
            return None
        for item in clist.find_all("span", class_="ead-chronitem"):
            date = item.find("span", class_="ead-date").get_text()
            group = item.find("span", class_="ead-eventgrp")
            events = [
                event.get_text()
                for event in group.find_all("span", class_="ead-event")
            ]
            items.add(item.name, {date: events}, item.sourceline)
        return items

    def chronlist_heading(self):
        clist = self.soup.find("span", class_="ead-chronlist")
        if not clist:
            return None
        return self.find_all("span", class_="ead-head", root=clist)

    def class_values(self, class_regex):
        return {
            util.clean_text(node.contents[0])
            for node in self.soup.find_all(class_=re.compile(class_regex))
        }

    @staticmethod
    def clean_dates(dates):
        return [
            re.sub(r",\s*(bulk|inclusive)\s*$", "", date).strip(f" {punc}")
            for date in dates
        ]

    def collection(self):
        return self.unittitle()

    def collection_unitid(self):
        return self.unitid()

    def _component(self):
        components = self.soup.find("section", class_="c-items")
        ids = []
        for c in components.find_all(
            "div", class_=re.compile(r"^level"), recursive=False
        ):
            ids.append(c["id"])
        return ids

    def component(self):
        regex = re.compile(r"^level")
        first_c = self.soup.find("div", class_=regex)
        if first_c is None:
            return []
        comps = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            cid = c["id"] if c.has_attr("id") else c.h1["id"]
            comps.append(comphtml.CompHTML(c, cid))
        return comps

    def component_id_level(self):
        regex = re.compile(r"^level")
        first_c = self.soup.find("div", class_=regex)
        if first_c is None:
            return []
        id_level = []
        for c in first_c.parent.find_all("div", class_=regex, recursive=False):
            cid = c["id"] if c.has_attr("id") else c.h1["id"]
            id_level.append((cid, re.split(r"[- ]", c["class"])[1]))
        return id_level

    def contents(self):
        return [text for text in self.soup.stripped_strings]

    def control_access_group(self, field):
        group = self.soup.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        result = ResultSet()
        for div in group.find_all("div"):
            result.add(
                div.name, util.clean_text(div.get_text()), div.sourceline
            )
        return result

    def control_access_group_val(self, field):
        group = self.soup.find("div", class_=f"controlaccess-{field}-group")
        if not group:
            return None
        result = ResultSet()
        for node in group.find_all(class_="controlaccess-value"):
            result.add(
                node.name, util.clean_text(node.get_text()), node.sourceline
            )
        return result

    def corpname(self):
        # return self.control_access_group("corpname")
        return list(
            {
                util.clean_text(corp_name.get_text())
                for corp_name in self.soup.find_all(
                    class_=re.compile(r"(ead-)?corpname$")
                )
            }
        )

    def creation_date(self):
        return util.clean_text(
            self.soup.find("div", class_="creation")
            .find(class_="ead-date")
            .get_text()
        )

    # def creator(self):
    #     creators = []
    #     for node in self.soup.find_all(
    #         "div", class_=re.compile(r"(corp|fam|pers)name role-Donor")
    #     ):
    #         donor = util.clean_text(node.contents[0])
    #         creators.append(donor)
    #     return sorted(creators)

    def creator(self):
        origination = self.soup.find(
            class_=re.compile(r"^md-group origination")
        )
        creators = [
            util.clean_text(node.contents[0])
            for node in origination.find_all(
                "div", class_=re.compile(r"^(corp|fam|pers)name")
            )
        ]
        return creators

    def creators(self):
        return self.creator()

    def custodhist(self):
        return self.formatted_note("custodhist")

    def dao(self):
        pass

    def dimensions(self):
        return self.formatted_note("dimensions")

    def eadid(self):
        return self.url().rstrip("/").split("/")[-1]

    def eadnum(self):
        return self.soup.find("span", class_="ead-num").get_text()

    def ead_class_values(self, class_name):
        return self.find_all(class_=f"ead-{class_name}", get_text=False)

    def editionstmt(self):
        return self.formatted_note("editionstmt")

    def extent(self):
        return self.formatted_note("extent")

    def famname(self):
        return [
            name.contents[0].strip()
            for name in self.soup.find_all("div", class_=re.compile("^famname"))
        ]

    def find_all(self, *args, root=None, get_text=True, **kwargs):
        if root is None:
            root = self.soup
        nodes = root.find_all(*args, **kwargs)
        if not nodes:
            return None
        find_expr = util.create_args_str(*args, **kwargs)
        result = ResultSet(xpath=find_expr)
        for node in nodes:
            text = node.get_text() if get_text else node.contents[0]
            text = util.clean_text(text)
            result.add(node.name, text, node.sourceline)
        return result

    def find_component(self, cid):
        node = self.soup.find(attrs={"id": cid})
        if node is not None:
            if node.name == "div":
                return comphtml.CompHTML(node, cid)
            elif node.name.startswith("h"):
                return comphtml.CompHTML(node.parent, cid)
            else:
                raise ValueError("Invalid tag for component")
        else:
            raise ComponentNotFoundError(
                f"Can't find {cid} in {self.html_file}"
            )

    def find_component_by_heading(self, head_id):
        head = self.soup.find(re.compile(r"^h\d$"), {"id": head_id})
        if head is not None:
            return comphtml.CompHTML(head.parent, head_id)
        else:
            raise ComponentNotFoundError(
                f"Can't find {head_id} in {self.html_file}"
            )

    def formatted_note(self, field):
        note = self.soup.find("div", class_=f"md-group formattednote {field}")
        if note is None:
            return None
        # text = note.div.p.get_text()
        for tag in ["div", "p"]:
            note_child = getattr(note, tag)
            if note_child is not None:
                # return note_child.get_text(strip=True)
                result = ResultSet()
                result.add(
                    note_child.name,
                    util.clean_text(note_child.get_text()),
                    note_child.sourceline,
                )
                return result
        return None

    def function(self):
        return self.control_access_group("function")

    def genreform(self):
        return self.control_access_group("genreform")

    def geogname(self):
        return self.control_access_group("geogname")

    def heading(self):
        return self.unittitle()

    def langcode(self):
        lang = pycountry.languages.get(name=self.language())
        return lang.alpha_3

    def language(self):
        return self.soup.find("div", class_="langusage").span.text

    def material_type(self):
        return self.genreform()

    def name(self):
        return list(
            {
                util.clean_text(node.get_text())
                for node in self.soup.find_all(class_="ead-name")
            }
        )

    def names(self):
        name_list = set()
        name_list.update(self.famname())
        name_list.update(self.class_values(r"^(ead-)?persname( role-Donor)?$"))

        regex = r"^(ead-)?corpname( role-Donor)?$"
        for node in self.soup.body.find_all(
            lambda tag: not re.search(
                r"repository", tag.parent.parent.get("class") or ""
            )
            and re.search(regex, tag.get("class") or "")
            or re.search(regex, tag.get("data-field") or "")
        ):
            name_list.add(util.clean_text(node.contents[0]))

        return sorted(name_list)

    def note(self):
        return self.formatted_note("notestmt")

    def occupation(self):
        return self.control_access_group("occupation")

    def odd(self):
        return self.formatted_note("odd")

    def persname(self):
        all_persnames = ResultSet()
        for persnames in [
            self.ead_class_values("persname"),
            self.control_access_group_val("persname"),
        ]:
            if persnames:
                all_persnames.append(persnames)
        if not all_persnames.isempty():
            return all_persnames
        else:
            return None

    def physfacet(self):
        return self.formatted_note("physfacet")

    def phystech(self):
        return self.formatted_note("phystech")

    def place(self):
        return self.control_access_group("geogname")

    def processinfo(self):
        return self.formatted_note("processinfo")

    def prefercite(self):
        return self.formatted_note("prefercite")

    def relatedmaterial(self):
        return self.formatted_note("relatedmaterial")

    def repository(self):
        return self.soup.find(
            "div", class_="md-group repository"
        ).div.get_text()

    def revisiondesc(self):
        return self.formatted_note("revisiondesc")

    def root(self):
        pass

    def scopecontent(self):
        return self.formatted_note("scopecontent")

    def separatedmaterial(self):
        return self.formatted_note("separatedmaterial")

    def series(self):
        pass

    def subject(self):
        return self.control_access_group("subject")

    def subjects(self):
        subj_set = ResultSet()
        for field in ['subject', 'function', 'occupation']:
            subjs = self.control_access_group(field)
            if subjs:
                subj_set.append(subjs)
        return subj_set if not subj_set.isempty() else None

    def subtitle(self):
        return self.soup.main.find(
            re.compile(r"^h\d$"), class_="subtitle"
        ).get_text()

    def title(self):
        titles = self.find_all(class_="ead-title")
        addl_title = self.control_access_group_val("title")
        if addl_title:
            titles.append(addl_title)
        return titles

    def title_head(self):
        title_str = self.soup.title.get_text(strip=True)
        return title_str

    def unitdate(self):
        return [
            date.text
            for date in self.soup.find("div", "md-group unit_date").find_all(
                "div"
            )
        ]

    def unitdate_all(self):
        return EADHTML.clean_dates(self.unitdate())

    def unitdate_bulk(self):
        return self.unitdate_grep(lambda date: "bulk" in date)

    def unitdate_grep(self, grep_func):
        return list(filter(grep_func, self.unitdate()))

    def unitdate_inclusive(self):
        return self.unitdate_grep(lambda date: "inclusive" in date)

    def unitdate_not_type(self):
        return self.unitdate_grep(
            lambda date: all(
                dtype not in date for dtype in ["bulk", "inclusive"]
            )
        )

    def unittitle(self):
        return self.soup.main.find(
            re.compile(r"^h\d$"), class_="page-title"
        ).get_text()

    def unitid(self):
        return self.soup.find("div", class_="md-group unit_id").div.get_text()

    def url(self):
        return self.soup.find("link", rel="canonical")["href"]

    def userestrict(self):
        return self.formatted_note("userestrict")
