# -*- coding: utf-8 -*-

# Standard library imports
from __future__ import unicode_literals

# Third party imports
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.test import TestCase

# Local application / specific library imports
from precise_bbcode import get_parser
from precise_bbcode.bbcode import BBCodeParserLoader
from precise_bbcode.bbcode.tag import BBCodeTag as ParserBBCodeTag
from precise_bbcode.bbcode.exceptions import InvalidBBCodePlaholder
from precise_bbcode.bbcode.exceptions import InvalidBBCodeTag
from precise_bbcode.models import BBCodeTag
from precise_bbcode.tag_pool import TagAlreadyCreated
from precise_bbcode.tag_pool import TagAlreadyRegistered
from precise_bbcode.tag_pool import TagNotRegistered
from precise_bbcode.tag_pool import tag_pool


class FooTag(ParserBBCodeTag):
    name = 'foo'

    class Options:
        render_embedded = False

    def render(self, value, option=None, parent=None):
        return '<pre>{}</pre>'.format(value)


class FooTagAlt(ParserBBCodeTag):
    name = 'fooalt'

    class Options:
        render_embedded = False

    def render(self, value, option=None, parent=None):
        return '<pre>{}</pre>'.format(value)


class FooTagSub(ParserBBCodeTag):
    name = 'foo2'

    class Options:
        render_embedded = False


class BarTag(ParserBBCodeTag):
    name = 'bar'

    def render(self, value, option=None, parent=None):
        if not option:
            return '<div class="bar">{}</div>'.format(value)
        return '<div class="bar" style="color:{};">{}</div>'.format(option, value)


class TestBbcodeTagPool(TestCase):
    TAGS_TESTS = (
        ('[fooalt]hello world![/fooalt]', '<pre>hello world!</pre>'),
        ('[bar]hello world![/bar]', '<div class="bar">hello world!</div>'),
        ('[fooalt]hello [bar]world![/bar][/fooalt]', '<pre>hello [bar]world![/bar]</pre>'),
        ('[bar]hello [fooalt]world![/fooalt][/bar]', '<div class="bar">hello <pre>world!</pre></div>'),
        ('[bar]안녕하세요![/bar]', '<div class="bar">안녕하세요!</div>'),
    )

    def setUp(self):
        self.parser = get_parser()

    def test_should_raise_if_a_tag_is_registered_twice(self):
        # Setup
        number_of_tags_before = len(tag_pool.get_tags())
        tag_pool.register_tag(FooTag)
        # Run & check
        # Let's add it a second time. We should catch an exception
        with self.assertRaises(TagAlreadyRegistered):
            tag_pool.register_tag(FooTag)
        # Let's make sure we have the same number of tags as before
        tag_pool.unregister_tag(FooTag)
        number_of_tags_after = len(tag_pool.get_tags())
        self.assertEqual(number_of_tags_before, number_of_tags_after)

    def test_cannot_register_tags_with_incorrect_parent_classes(self):
        # Setup
        number_of_tags_before = len(tag_pool.get_tags())
        # Run & check
        with self.assertRaises(ImproperlyConfigured):
            class ErrnoneousTag4:
                pass
            tag_pool.register_tag(ErrnoneousTag4)
        number_of_tags_after = len(tag_pool.get_tags())
        self.assertEqual(number_of_tags_before, number_of_tags_after)

    def test_cannot_register_tags_that_are_already_stored_in_the_database(self):
        # Setup
        BBCodeTag.objects.create(
            tag_definition='[tt]{TEXT}[/tt]', html_replacement='<span>{TEXT}</span>')
        # Run
        with self.assertRaises(TagAlreadyCreated):
            class ErrnoneousTag9(ParserBBCodeTag):
                name = 'tt'
                definition_string = '[tt]{TEXT}[/tt]'
                format_string = '<span>{TEXT}</span>'
            tag_pool.register_tag(ErrnoneousTag9)

    def test_cannot_unregister_a_non_registered_tag(self):
        # Setup
        number_of_tags_before = len(tag_pool.get_tags())
        # Run & check
        with self.assertRaises(TagNotRegistered):
            tag_pool.unregister_tag(FooTagSub)
        number_of_tags_after = len(tag_pool.get_tags())
        self.assertEqual(number_of_tags_before, number_of_tags_after)

    def test_tags_can_be_rendered(self):
        # Setup
        parser_loader = BBCodeParserLoader(parser=self.parser)
        tag_pool.register_tag(FooTagAlt)
        tag_pool.register_tag(BarTag)
        parser_loader.init_bbcode_tags()
        # Run & check
        for bbcodes_text, expected_html_text in self.TAGS_TESTS:
            result = self.parser.render(bbcodes_text)
            self.assertEqual(result, expected_html_text)


class TestBbcodeTag(TestCase):
    def setUp(self):
        self.parser = get_parser()

    def test_that_are_invalid_should_raise_at_runtime(self):
        # Run & check
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag1(ParserBBCodeTag):
                pass
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag2(ParserBBCodeTag):
                delattr(ParserBBCodeTag, 'name')
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag3(ParserBBCodeTag):
                name = 'it\'s a bad tag name'
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag4(ParserBBCodeTag):
                name = 'ooo'
                definition_string = '[ooo]{TEXT}[/ooo]'
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag5(ParserBBCodeTag):
                name = 'ooo'
                definition_string = 'bad definition'
                format_string = 'bad format string'
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag6(ParserBBCodeTag):
                name = 'ooo'
                definition_string = '[ooo]{TEXT}[/aaa]'
                format_string = 'bad format string'
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag7(ParserBBCodeTag):
                name = 'ooo'
                definition_string = '[ooo]{TEXT}[/ooo]'
                format_string = '<span></span>'
        with self.assertRaises(InvalidBBCodeTag):
            class ErrnoneousTag8(ParserBBCodeTag):
                name = 'ooo'
                definition_string = '[ooo={TEXT}]{TEXT}[/ooo]'
                format_string = '<span>{TEXT}</span>'

    def test_containing_invalid_placeholders_should_raise_during_rendering(self):
        # Setup
        class TagWithInvalidPlaceholders(ParserBBCodeTag):
            name = 'bad'
            definition_string = '[bad]{FOOD}[/bad]'
            format_string = '<span>{FOOD}</span>'
        self.parser.add_bbcode_tag(TagWithInvalidPlaceholders)
        # Run
        with self.assertRaises(InvalidBBCodePlaholder):
            self.parser.render('[bad]apple[/bad]')


class TestDbBbcodeTag(TestCase):
    ERRONEOUS_TAGS_TESTS = (
        {'tag_definition': '[tag]', 'html_replacement': ''},
        {'tag_definition': 'it\s not a tag', 'html_replacement': ''},
        {'tag_definition': '[first]{TEXT1}[/end]', 'html_replacement': '<p>{TEXT1}</p>'},
        {'tag_definition': '[t2y={TEXT1}]{TEXT1}[/t2y]', 'html_replacement': '<b>{TEXT1}</b>'},
        {'tag_definition': '[tag2]{TEXT1}[/tag2]', 'html_replacement': '<p>{TEXT1}</p>', 'standalone': True},
        {'tag_definition': '[start]{TEXT1}[/end]', 'html_replacement': '<p>{TEXT1}</p>'},
        {'tag_definition': '[start]{TEXT1}[/end]', 'html_replacement': '<p>{TEXT1}</p>'},
        {'tag_definition': '[start]{TEXT1}[/end]', 'html_replacement': '<p>{TEXT2}</p>'},
        {'tag_definition': '[start={TEXT1}]{TEXT1}[/end]', 'html_replacement': '<p style="color:{TEXT1};">{TEXT1}</p>'},
        {'tag_definition': '[justify]{TEXT1}[/justify]', 'html_replacement': '<div style="text-align:justify;"></div>'},
        {'tag_definition': '[center][/center]', 'html_replacement': '<div style="text-align:center;">{TEXT1}</div>'},
        {'tag_definition': '[spe={COLOR}]{TEXT}[/spe]', 'html_replacement': '<div class="spe">{TEXT}</div>'},
        {'tag_definition': '[spe]{TEXT}[/spe]', 'html_replacement': '<div class="spe" style="color:{COLOR};">{TEXT}</div>'},
        {'tag_definition': '[spe]{UNKNOWN}[/spe]', 'html_replacement': '<div>{UNKNOWN}</div>'},
        {'tag_definition': '[io]{TEXT#1}[/io]', 'html_replacement': '<span>{TEXT#1}</span>'},
        {'tag_definition': '[io]{TEXTa}[/io]', 'html_replacement': '<span>{TEXTb}</span>'},
        {'tag_definition': '[ test]{TEXT1}[/test]', 'html_replacement': '<span>{TEXT}</span>'},
        {'tag_definition': '[test ]{TEXT1}[/test]', 'html_replacement': '<span>{TEXT}</span>'},
        {'tag_definition': '[test]{TEXT1}[/ test ]', 'html_replacement': '<span>{TEXT}</span>'},
        {'tag_definition': '[test]{TEXT1}[/test ]', 'html_replacement': '<span>{TEXT}</span>'},
        {'tag_definition': '[foo]{TEXT1}[/foo ]', 'html_replacement': '<span>{TEXT}</span>'},
        {'tag_definition': '[bar]{TEXT}[/bar]', 'html_replacement': '<span>{TEXT}</span>'},  # Already registered
    )

    VALID_TAG_TESTS = (
        {'tag_definition': '[pre]{TEXT}[/pre]', 'html_replacement': '<pre>{TEXT}</pre>'},
        {'tag_definition': '[pre2={COLOR}]{TEXT1}[/pre2]', 'html_replacement': '<pre style="color:{COLOR};">{TEXT1}</pre>'},
        {'tag_definition': '[hrcustom]', 'html_replacement': '<hr />', 'standalone': True},
        {'tag_definition': '[oo]{TEXT}', 'html_replacement': '<li>{TEXT}</li>', 'same_tag_closes': True},
        {'tag_definition': '[h]{TEXT}[/h]', 'html_replacement': '<strong>{TEXT}</strong>', 'helpline': 'Display your text in bold'},
        {'tag_definition': '[hbold]{TEXT}[/hbold]', 'html_replacement': '<strong>{TEXT}</strong>', 'display_on_editor': False},
        {'tag_definition': '[pre3]{TEXT}[/pre3]', 'html_replacement': '<pre>{TEXT}</pre>', 'newline_closes': True},
        {'tag_definition': '[pre4]{TEXT}[/pre4]', 'html_replacement': '<pre>{TEXT}</pre>', 'same_tag_closes': True},
        {'tag_definition': '[troll]{TEXT}[/troll]', 'html_replacement': '<div class="troll">{TEXT}</div>', 'end_tag_closes': True},
        {'tag_definition': '[troll1]{TEXT}[/troll1]', 'html_replacement': '<div class="troll">{TEXT}</div>', 'transform_newlines': True},
        {'tag_definition': '[idea]{TEXT1}[/idea]', 'html_replacement': '<div class="idea">{TEXT1}</div>', 'render_embedded': False},
        {'tag_definition': '[idea1]{TEXT1}[/idea1]', 'html_replacement': '<div class="idea">{TEXT1}</div>', 'escape_html': False},
        {'tag_definition': '[link]{URL}[/link]', 'html_replacement': '<div class="idea">{URL}</div>', 'replace_links': False},
        {'tag_definition': '[link1]{URL}[/link1]', 'html_replacement': '<div class="idea">{URL}</div>', 'strip': True},
        {'tag_definition': '[mailto]{EMAIL}[/mailto]', 'html_replacement': '<a href="mailto:{EMAIL}">{EMAIL}</a>', 'swallow_trailing_newline': True},
        {'tag_definition': '[food]{CHOICE=apple,tomato,orange}[/food]', 'html_replacement': '<span>{CHOICE=apple,tomato,orange}</span>'},
        {'tag_definition': '[food++={CHOICE2=red,blue}]{CHOICE1=apple,tomato,orange}[/food++]', 'html_replacement': '<span data-choice="{CHOICE2=red,blue}">{CHOICE1=apple,tomato,orange}</span>'},
        {'tag_definition': '[big]{RANGE=2,15}[/big]', 'html_replacement': '<span>{RANGE=2,15}</span>'},
        {'tag_definition': '[b]{TEXT}[/b]', 'html_replacement': '<b>{TEXT}</b>'},  # Default tag overriding
    )

    def setUp(self):
        self.parser = get_parser()

    def test_should_not_save_invalid_tags(self):
        # Run & check
        for tag_dict in self.ERRONEOUS_TAGS_TESTS:
            with self.assertRaises(ValidationError):
                tag = BBCodeTag(**tag_dict)
                tag.clean()

    def test_should_save_valid_tags(self):
        # Run & check
        for tag_dict in self.VALID_TAG_TESTS:
            tag = BBCodeTag(**tag_dict)
            try:
                tag.clean()
            except ValidationError:
                self.fail('The following BBCode failed to validate: {}'.format(tag_dict))

    def test_should_save_default_bbcode_tags_rewrites(self):
        # Setup
        tag = BBCodeTag(tag_definition='[b]{TEXT1}[/b]', html_replacement='<b>{TEXT1}</b>')
        # Run & check
        try:
            tag.clean()
        except ValidationError:
            self.fail('The following BBCode failed to validate: {}'.format(tag))

    def test_should_provide_the_required_parser_bbcode_tag_class(self):
        # Setup
        tag = BBCodeTag(**{'tag_definition': '[io]{TEXT}[/io]', 'html_replacement': '<b>{TEXT}</b>'})
        tag.save()
        # Run & check
        parser_tag_klass = tag.parser_tag_klass
        self.assertTrue(issubclass(parser_tag_klass, ParserBBCodeTag))
        self.assertEqual(parser_tag_klass.name, 'io')
        self.assertEqual(parser_tag_klass.definition_string, '[io]{TEXT}[/io]')
        self.assertEqual(parser_tag_klass.format_string, '<b>{TEXT}</b>')

    def test_can_be_rendered_by_the_bbcode_parser(self):
        # Setup
        parser_loader = BBCodeParserLoader(parser=self.parser)
        tag = BBCodeTag(**{'tag_definition': '[mail]{EMAIL}[/mail]',
                        'html_replacement': '<a href="mailto:{EMAIL}">{EMAIL}</a>', 'swallow_trailing_newline': True})
        tag.save()
        parser_loader.init_custom_bbcode_tags()
        # Run & check
        self.assertEqual(self.parser.render('[mail]xyz@xyz.com[/mail]'), '<a href="mailto:xyz@xyz.com">xyz@xyz.com</a>')
