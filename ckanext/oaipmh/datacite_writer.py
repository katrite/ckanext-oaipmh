from iso639 import languages
from lxml.etree import SubElement
from oaipmh.server import NS_XSI

NS_OAIDATACITE = 'http://schema.datacite.org/oai/oai-1.0/'
NS_DATACITE = 'http://schema.datacite.org/meta/kernel-3.1/'
event_to_dt = {'collection': 'Collected',
               'creation': 'Created',
               'extended': 'Updated',
               'changed': 'Updated',
               'published': 'Issued',
               'sent': 'Submitted',
               'received': 'Accepted',
               'modified': 'Updated'}


def _convert_language(lang):
    '''
    Convert alpha2 language (eg. 'en') to terminology language (eg. 'eng')
    '''
    try:
        lang_object = languages.get(part2t=lang)
        return lang_object.part1
    except KeyError as ke:
        # TODO: Parse ISO 639-2 B/T ?
        # log.debug('Invalid language: {ke}'.format(ke=ke))
        return ''


def _append_agent(e_agent_parent, role, key, value, roletype=None):
    for agent in value:
        e_agent = SubElement(e_agent_parent, nsdatacite(role))
        if roletype:
            e_agent.set(role + 'Type', roletype)
        agentname = role + 'Name'
        e_agent_name = SubElement(e_agent, nsdatacite(agentname))
        e_agent_name.text = agent['name']
        org = agent.get('organisation')
        if org:
            e_affiliation = SubElement(e_agent, nsdatacite('affiliation'))
            e_affiliation.text = org


def datacite_writer(element, metadata):
    '''Transform oaipmh.common.Metadata metadata dictionaries to lxml.etree.Element XML documents.
    '''
    e_dc = SubElement(element, nsoaidatacite('oai_datacite'),
                      nsmap = {None: NS_OAIDATACITE, 'xsi': NS_XSI})
    e_dc.set('{%s}schemaLocation' % NS_XSI, '%s http://schema.datacite.org/oai/oai-1.0/oai.xsd' % NS_OAIDATACITE)
    e_irq = SubElement(e_dc, nsoaidatacite('isReferenceQuality'))
    e_irq.text = 'false'
    e_sv = SubElement(e_dc, nsoaidatacite('schemaVersion'))
    e_sv.text = '3.1'
    e_ds = SubElement(e_dc, nsoaidatacite('datacentreSymbol'))
    e_ds.text = 'EUDAT B2FIND'
    e_pl = SubElement(e_dc, nsoaidatacite('payload'))
    e_r = SubElement(e_pl, nsdatacite('resource'), nsmap = {None: NS_DATACITE, 'xsi': NS_XSI})
    e_r.set('{%s}schemaLocation' % NS_XSI, '%s http://schema.datacite.org/meta/kernel-3/metadata.xsd' % NS_DATACITE)

    map = metadata.getMap()
    for k, v in map.iteritems():
        if v:
            if '/@' in k:
                continue
            if k == 'creators':
                e_agent_parent = SubElement(e_r, nsdatacite('creators'))
                _append_agent(e_agent_parent, 'creator', k, v)
                continue
            if k == 'titles':
                primary_lang = 'eng'
                e_titles = SubElement(e_r, nsdatacite(k))
                e_title_primary = SubElement(e_titles, nsdatacite('title'))
                e_title_primary.text = v[0]
                """title_langs = v[0].keys()
                if primary_lang in title_langs:
                    lang = _convert_language(primary_lang)
                    e_title_primary.set('lang', lang)
                    e_title_primary.text = v[0][primary_lang]
                    for l in title_langs:
                        if l != primary_lang:
                            e_title_translated = SubElement(e_titles, nsdatacite('title'))
                            e_title_translated.set('lang', _convert_language(l))
                            e_title_translated.set('titleType', 'TranslatedTitle')
                            e_title_translated.text = v[0][l]
                else:
                    e_title_primary.set('lang', _convert_language(title_langs[0]))
                    e_title_primary.text = v[0][title_langs[0]]
                    for l in title_langs[1:]:
                        e_title_translated = SubElement(e_titles, nsdatacite('title'))
                        e_title_translated.set('lang', _convert_language(l))
                        e_title_translated.set('titleType', 'TranslatedTitle')
                        e_title_translated.text = v[0][l]"""
                continue
            if k == 'subjects':
                e_subjects = SubElement(e_r, nsdatacite(k))
                for subject in v:
                    e_subject = SubElement(e_subjects, nsdatacite('subject'))
                    e_subject.text = subject
                continue
            if k == 'contributors':
                e_agent_parent = e_r.find(".//{*}" + 'contributors')
                if not e_agent_parent:
                    e_agent_parent = SubElement(e_r, nsdatacite('contributors'))
                _append_agent(e_agent_parent, 'contributor', k, v, 'Other')
                continue
            if k == 'funders':
                if v[0].get('organisation') or v[0].get('name'):
                    e_agent_parent = e_r.find(".//{*}" + 'contributors')
                    if not e_agent_parent:
                        e_agent_parent = SubElement(e_r, nsdatacite('contributors'))
                    for agent in v:
                        e_agent = SubElement(e_agent_parent, nsdatacite('contributor'))
                        e_agent.set('contributorType', 'Funder')
                        e_agent_name = SubElement(e_agent, nsdatacite('contributorName'))
                        e_agent_name.text = agent.get('organisation') or agent.get('name')
                continue
            if k == 'dates':
                e_dates = SubElement(e_r, nsdatacite(k))
                for event in v:
                    e_date = SubElement(e_dates, nsdatacite('date'))
                    e_date.text = event['when']
                    e_date.set('dateType', event_to_dt[event['type']])
                continue
            e = SubElement(e_r, nsdatacite(k))
            e.text = v[0] if isinstance(v, list) else v

    for k, v in map.iteritems():
        if '/@' in k:
            element, attr = k.split('/@')
            print(e_r.tag)
            e = e_r.find(".//{*}" + element, )
            if e is not None:
                e.set(attr, v[0] if isinstance(v, list) else v)


def nsdatacite(name):
    return '{%s}%s' % (NS_DATACITE, name)


def nsoaidatacite(name):
    return '{%s}%s' % (NS_OAIDATACITE, name)