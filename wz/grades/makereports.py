### python >= 3.7
# -*- coding: utf-8 -*-

"""
grades/makereports.py

Last updated:  2021-04-29

Generate the grade reports for a given group and "term".
Fields in template files are replaced by the report information.

In the templates there are grouped and numbered slots for subject names
and the corresponding grades.

=+LICENCE=============================
Copyright 2021 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

=-LICENCE========================================
"""

#TODO: Sonderzeugnisse

#TODO: Maybe also "Sozialverhalten" und "Arbeitsverhalten"
#TODO: Praktika? e.g.
#       Vermessungspraktikum:   10 Tage
#       Sozialpraktikum:        3 Wochen
#TODO: Maybe component courses (& eurythmy?) merely as "teilgenommen"?

_REPORT_TYPE_FIELD = '+ZA'

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

## Messages
_NOT_COMPLETE = "Daten für {pupil} unvollständig"
_NO_REPORT_TYPE = "Kein Zeugnistyp für Schüler {pids}"
_MULTI_GRADE_GROUPS = "Fach {sbj} passt zu mehr als eine Fach-Gruppe"
_NO_GRADE = "Schüler {pname}: keine Note im Fach {sbj}"
_UNEXPECTED_GRADE_GROUP = "Ungültiger Fachgruppe ({tag}) in Vorlage:\n" \
        "  {tpath}"
_NO_SUBJECT_GROUP = "Keine passende Fach-Gruppe für Fach {sbj}"
_NO_SLOT = "Kein Platz mehr für Fach mit Kürzel {sid} in Fachgruppe {tag}." \
        " Bisher: {done}"
_BAD_REPORT_TYPE = "Ungültiger Zeugnistyp: '{rtype}'"


from core.base import Dates
from core.pupils import PUPILS, sortkey
from local.base_config import year_path, class_year, \
        print_schoolyear, LINEBREAK
from local.grade_config import UNCHOSEN, MISSING_GRADE, NO_GRADE, UNGRADED, \
        GradeConfigError, NO_SUBJECT, GradeBase
from local.abitur_config import AbiCalc
from local.grade_template import info_extend
from template_engine.template_sub import Template, TemplateError
from grades.gradetable import GradeTable, GradeTableError


class GradeReports:
    """Generate the grade reports for a group of pupils.
    The group must be a valid grade-report group (which can be a class
    name or a class name with a group tag, e.g. '12.G') – the valid
    groups are specified (possibly dependant on the term) in the
    'GRADE_TERMS' configuration file.
    The grade information is extracted from the database for the given
    school-year and "term".
    """
    def __init__(self, schoolyear, group, term, tag):
        self.grade_table = GradeTable(schoolyear, group, term, tag)
        self.gmap0 = {  ## data shared by all pupils in the group
            'GROUP': group,
            'TERM': term,
#            'CYEAR': class_year(group),
#            'issue_d': self.grade_table.issue_d,  # for file-names
#            'ISSUE_D': Dates.print_date(self.grade_table.issue_d,
#                    trap = False),
            'ISSUE_D': self.grade_table.issue_d,
            'GRADES_D': self.grade_table.grades_d,
#            'GRADES_D': Dates.print_date(self.grade_table.grades_d,
#                    trap = False),
            'SCHOOL': SCHOOL_DATA['SCHOOL_NAME'],
#            'SCHOOLBIG': SCHOOL_DATA['SCHOOL_NAME'].upper(),
#            'schoolyear': schoolyear,
#            'SCHOOLYEAR': print_schoolyear(schoolyear)
            'SCHOOLYEAR': schoolyear
        }
#
    def makeReports(self, pids = None):
        """A subset of the group can be chosen by passing a list of
        pupil-ids as <pids>.
        The resulting pdfs will be combined into a single pdf-file for
        each report type. If the reports are double-sided, empty pages
        can be added as necessary.
        Return a list of file-paths for the report-type pdf-files.
        """
        greport_type = {}
        no_report_type = []
        if self.grade_table.term == 'Abitur':
            self.abicalc = {}
#TODO: Could the Abi calculations be instigated by the template configuration?

        for pid, grades in self.grade_table.items():
            # <forGroupTerm> accepts only valid grade-groups.
            # Check pupil filter, <pids>:
            if pids and (pid not in pids):
                continue
            if self.grade_table.term == 'Abitur':
                _ac = AbiCalc(self.grade_table, pid)
                _acc = _ac.calculate()
                self.abicalc[pid] = (_ac, _acc)
                rtype = _acc['REPORT_TYPE']
                if not rtype:
                    REPORT("ERROR", _NOT_COMPLETE.format(
                            pupil = self.grade_table.name[pid]))
            else:
                # Split group according to report type
                rtype = grades.get(_REPORT_TYPE_FIELD, '-')
            if rtype:
                try:
                    greport_type[rtype].append(pid)
                except KeyError:
                    greport_type[rtype] = [pid]
            else:
                no_report_type.append(pid)
        if no_report_type:
            raise GradeTableError(_NO_REPORT_TYPE.format(
                    pids = ', '.join(no_report_type)))

        ### Build reports for each report-type separately
        fplist = []
        for rtype, pid_list in greport_type.items():
            if rtype == '-':
                continue        # Skip these pupils
            _tg = self.prepare_report_data(rtype, pid_list)
            if _tg:
                template, gmaplist = _tg
                # make_pdf: data_list, dir_name, working_dir, double_sided
                fplist.append(template.make_pdf(gmaplist,
                        grades.report_name(
                                group = self.grade_table.group,
                                term = self.grade_table.term,
                                subselect = self.grade_table.subselect,
                                rtype = rtype
                        ),
                        year_path(self.grade_table.schoolyear,
                            grades.REPORT_DIR.format(
                                term = self.grade_table.term)
                        ),
                        double_sided = grades.double_sided(
                                self.grade_table.group, rtype)
                ))
        return fplist
#
    def prepare_report_data(self, rtype, pid_list):
        """Prepare the slot-mappings for report generation.
        Return a tuple: (template object, list of slot-mappings).
        """
        ### Pupil data
        pupils = PUPILS(self.grade_table.schoolyear)
        # The individual pupil data can be fetched using pupils[pid].
        # Fetching the whole class may not be good enough, as it is vaguely
        # possible that a pupil has changed class.
        # The subject data is available at <self.grade_table.subjects>
        # and <self.sid2subject_data>.
        ### Grade report template
        try:
            template_tag = GradeBase.report_template(
                    self.grade_table.group, rtype)
        except GradeConfigError:
            REPORT('ERROR', _BAD_REPORT_TYPE.format(rtype = rtype))
            return None
        gTemplate = Template(template_tag)
        ### Build the data mappings and generate the reports
        gmaplist = []
        for pid in pid_list:
            gmap = self.gmap0.copy()
            # Add pupil data
            pdata = pupils[pid]
            gmap.update(pdata)
            # Alphabetical name-tag
            gmap['PSORT'] = sortkey(pdata)

            grades = self.grade_table[pid]
            # Grade parameters
            gmap['STREAM'] = grades.stream
            gmap['SekII'] = grades.sekII
#            comment = grades.pop('+B', '')
#            if comment:
#                comment = comment.replace(LINEBREAK, '\n')
#            gmap['COMMENT'] = comment

            ## Process the grades themselves ...
            if self.grade_table.term == 'Abitur':
                _ac, _acc = self.abicalc[pid]
#                showgrades = {k: UNGRADED if v == NO_GRADE else v
#                        for k, v in _ac.tags.items()}
#                gmap.update(showgrades)
                gmap.update(_ac.tags)
                gmap.update(_acc)
            else:
                # Sort into grade groups
                grade_map = self.sort_grade_keys(pupils.name(pdata),
                        grades, gTemplate)
                gmap.update(grade_map)
                gmap['REPORT_TYPE'] = rtype

            ## Add template and "local" stuff
            info_extend(gmap)
            gmaplist.append(gmap)

        return (gTemplate, gmaplist)
#

#TODO: Could this be instigated / driven by the template configuration?
# E.g. Field type GRADE_GROUP + G looks for the next subject/grade in
# group G? If the subjects need to be searched, perhaps a cache could help?
    def sort_grade_keys(self, name, grades, template):
        """Allocate the subjects and grades to the appropriate slots in the
        template.
        Return a {slot: grade-entry} mapping.
        <grades> is the <Grades> instance,
        <template> is a <Template> (or subclass) instance.
        """
        _keys = template.all_keys()
        _grp2indexes = group_grades(_keys)
        for rg in grades.group_info(self.grade_table.group, 'Nullgruppen'):
            _grp2indexes[rg] = None
        sbj_grades = _grp2indexes[None] # "direct" grade slots
        gmap = {}   # for the result
        for sid, grade in grades.items():
            # Get the print representation of the grade
            if sid[0] == '+':
                gmap[sid] = grade
                continue
            g = grades.print_grade(grade)
            if sbj_grades:
                try:
                    sbj_grades.remove(sdata.sid)
                except KeyError:
                    pass
                else:
                    # grade-only entry
                    gmap['G.%s' % sdata.sid] = g or UNGRADED
                    continue
            if grade == UNCHOSEN:
                continue
            # Get the subject data
            sdata = self.grade_table.sid2subject_data[sid]
            if g == MISSING_GRADE:
                REPORT("WARN", _NO_GRADE.format(pname = name,
                        sbj = sdata.name))
            if not g:
                # Subject "not chosen", no report entry
                continue
            done = False
            for rg in sdata.report_groups:
                # Get an index
                try:
                    ilist = _grp2indexes[rg]
                except KeyError:
                    continue
                if done:
                    raise GradeConfigError(_MULTI_GRADE_GROUPS.format(
                            sbj = sbj))
                done = True
                if ilist == None:
                    # Suppress subject/grade
                    continue
                try:
                    i = ilist.pop()
                except IndexError as e:
                    # No indexes left
                    raise TemplateError(_NO_SLOT.format(tag = rg,
                            sid = sdata.sid, done = repr(gmap))) from e
                gmap['G.%s.%s' % (rg, i)] = g
                # For the name, strip possible extra bits, after '|':
                gmap['S.%s.%s' % (rg, i)] = sdata.name.split(
                        '|', 1)[0].rstrip()
            if not done:
                raise GradeConfigError(_NO_SUBJECT_GROUP.format(
                        sbj = sdata.name))
        # Fill unused slots
        if sbj_grades:
            for sid in sbj_grades:
                gmap['G.%s' % sid] = UNGRADED
        for tag, ilist in _grp2indexes.items():
            if ilist:
                for i in ilist:
                    gmap['G.%s.%s' % (tag, i)] = NO_SUBJECT
                    gmap['S.%s.%s' % (tag, i)] = NO_SUBJECT
        return gmap

###

def group_grades(all_keys):
    """Determine the subject and grade slots in the template.
    <all_keys> is the complete set of template slots/keys.
    Keys of the form 'G.k.n' are sought: k is the group-tag, n is a number.
    Return a mapping {group-tag -> [index, ...]}.
    The index lists are sorted reverse-alphabetically (for popping).
    Note that the indexes are <str> values, not <int>.
    Also keys of the form 'G.sid' are collected as a set. Such keys are
    returned as the value of the entry with <group-tag = None>.
    """
#    G_REGEXP = re.compile(r'G\.([A-Za-z]+)\.([0-9]+)$')
    tags = {}
    subjects = set()
    for key in all_keys:
        if key.startswith('G.'):
            ksplit = key.split('.')
            if len(ksplit) == 3:
                # G.<group tag>.<index>
                tag, index = ksplit[1], ksplit[2]
                try:
                    tags[tag].add(index)
                except KeyError:
                    tags[tag] = {index}
            elif len(ksplit) == 2:
                # G.<subject tag>
                gsubjects.add(ksplit[1])
    result = {None: subjects}
    for tag, ilist in tags.items():
        result[tag] = sorted(ilist, reverse = True)
    return result


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()

    _year = '2016'

    # Build reports for a group
#    greports = GradeReports(_year, '13', 'Abitur', None)
    greports = GradeReports(_year, '11.G', '2._Halbjahr', None)
#    greports = GradeReports(_year, '13', '1._Halbjahr', None)
    for f in greports.makeReports():
        print("\n$$$: %s\n" % f)
