from bson.objectid import ObjectId

import colander
from colander import Email
from colander import Integer
from colander import SchemaNode
from colander import SequenceSchema
from colander import String

from deform import Button
from deform import Form
from deform.widget import SequenceWidget
from deform.widget import TextAreaWidget

from deform_ext_autocomplete import ExtendedAutocompleteInputWidget

from pyramid_deform import CSRFSchema

from mnemos.i18n import _
from mnemos.utils import get_full_name


class EmailSequence(SequenceSchema):
    email = SchemaNode(String(), title=_('E-mail'), validator=Email())


class TelephoneSequence(SequenceSchema):
    telephone = SchemaNode(String(), title=_('Telephone'))


@colander.deferred
def deferred_autocomplete_widget(node, kw):
    """Return an instance of ``ExtendedAutocompleteInputWidget`` where
    the ``display_value`` callable has access to the database
    connection through the request.
    """
    request = kw['request']
    def display_value(field, cstruct):
        if not cstruct:
            return cstruct
        obj_id = ObjectId(cstruct)
        contact = request.db.contacts.find_one({'_id': obj_id})
        if not contact:
            return ''
        return get_full_name(contact)
    return ExtendedAutocompleteInputWidget(values='/ajax_search',
                                           display_value=display_value)


class LinkSequence(SequenceSchema):
    link = SchemaNode(
        String(),
        title=_('Link'),
        widget=deferred_autocomplete_widget)


class ContactSchema(CSRFSchema):
    last_name = SchemaNode(String(), title=_('Last name'))
    first_name = SchemaNode(String(), title=_('First name'))
    emails = EmailSequence(
        title=_('E-mail addresses'),
        missing=(),
        widget=SequenceWidget(
            add_subitem_text_template=_('Add e-mail address')))
    telephones = TelephoneSequence(
        title=_('Telephone numbers'),
        missing=(),
        widget=SequenceWidget(
            add_subitem_text_template=_('Add telephone number')))
    address = SchemaNode(String(),
                         title=_('Address'),
                         widget=TextAreaWidget(cols=50, rows=3),
                         missing='')
    postal_code = SchemaNode(String(), title=_('Postal code'), missing='')
    city = SchemaNode(String(), title=_('City'), missing='')
    country = SchemaNode(String(), title=_('Country'), missing='')
    door_code = SchemaNode(String(), title=_('Door code'), missing='')
    coord = SchemaNode(
        String(),
        title=_('Coordinates'),
        description=_('Coordinates will be automatically filled. '
                      'You should not have to provide them manually.'),
        missing='')
    birth_day = SchemaNode(Integer(),
                           title=_('Birth day'),
                           missing=0)
    birth_month = SchemaNode(Integer(),
                             title=_('Birth month'),
                             missing=0)
    birth_year = SchemaNode(Integer(),
                            title=_('Birth year'),
                            missing=0)
    notes = SchemaNode(String(),
                       title=_('Notes'),
                       widget=TextAreaWidget(cols=50, rows=3),
                       missing='')
    links = LinkSequence(
        title=_('Links'),
        missing=(),
        widget=SequenceWidget(
            add_subitem_text_template=_('Add link')))


def make_add_form(request):
    schema = ContactSchema().bind(request=request)
    return Form(schema,
                buttons=(Button(title=_('Add')), ))


def make_edit_form(request, action):
    schema = ContactSchema().bind(request=request)
    return Form(schema,
                action=action,
                formid='edit-form',
                buttons=(Button(title=_('Save changes')), ))
