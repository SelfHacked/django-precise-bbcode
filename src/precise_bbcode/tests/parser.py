# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django.test import TestCase

# Local application / specific library imports
from precise_bbcode.parser import BBCodeParser


class ParserTestCase(TestCase):
    DEFAULT_TAGS_RENDERING_TESTS = (
        # BBcodes without errors
        ('[b]hello world![/b]', '<strong>hello world!</strong>'),
        ('[b]hello [i]world![/i][/b]', '<strong>hello <em>world!</em></strong>'),
        ('[b]hello [ world![/b]', '<strong>hello [ world!</strong>'),
        ('[b]]he[llo [ w]orld![/b]', '<strong>]he[llo [ w]orld!</strong>'),
        ('[ b ]hello [u]world![/u][ /b ]', '<strong>hello <u>world!</u></strong>'),
        ('[b]hello [] world![/b]', '<strong>hello [] world!</strong>'),
        ('[list]\n[*]one\n[*]two\n[/list]', '<ul><li>one</li><li>two</li></ul>'),
        ('[list=1]\n[*]item 1\n[*]item 2\n[/list]', '<ol style="list-style-type:decimal;"><li>item 1</li><li>item 2</li></ol>'),
        ('[list] [*]Item 1 [*]Item 2 [*]Item 3   [/list]', '<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>'),
        ('>> some special chars >< <>', '&gt;&gt; some special chars &gt;&lt; &lt;&gt;'),
        ('"quoted text"', '&quot;quoted text&quot;'),
        ('>> some other special chars', '&gt;&gt; some other special chars'),
        ('[url]http://foo.com/bar.php?some--data[/url]', '<a href="http://foo.com/bar.php?some--data">http://foo.com/bar.php?some--data</a>'),
        ('[url]http://www.google.com[/url]', '<a href="http://www.google.com">http://www.google.com</a>'),
        ('[url=google.com]goto google[/url]', '<a href="http://google.com">goto google</a>'),
        ('[url=http://google.com][/url]', '<a href="http://google.com">http://google.com</a>'),
        ('[URL=google.com]goto google[/URL]', '<a href="http://google.com">goto google</a>'),
        ('[url=<script>alert(1);</script>]xss[/url]', '<a href="&lt;script&gt;alert(1);&lt;/script&gt;">xss</a>'),
        ('www.google.com foo.com/bar http://xyz.ci', '<a href="http://www.google.com">www.google.com</a> <a href="http://foo.com/bar">foo.com/bar</a> <a href="http://xyz.ci">http://xyz.ci</a>'),
        ('[url=relative/foo/bar.html]link[/url]', '<a href="relative/foo/bar.html">link</a>'),
        ('[url=/absolute/foo/bar.html]link[/url]', '<a href="/absolute/foo/bar.html">link</a>'),
        ('[url=./hello.html]world![/url]', '<a href="./hello.html">world!</a>'),
        ('[img]http://www.foo.com/bar/img.png[/img]', '<img src="http://www.foo.com/bar/img.png" alt="" />'),
        ('[quote] \r\nhello\nworld! [/quote]', '<blockquote>hello<br />world!</blockquote>'),
        ('[code][b]hello world![/b][/code]', '<code>[b]hello world![/b]</code>'),
        ('[color=green]goto [url=google.com]google website[/url][/color]', '<span style="color:green;">goto <a href="http://google.com">google website</a></span>'),
        ('[color=#FFFFFF]white[/color]', '<span style="color:#FFFFFF;">white</span>'),
        ('[color=<script></script>]xss[/color]', '[color=&lt;script&gt;&lt;/script&gt;]xss[/color]'),
        ('[COLOR=blue]hello world![/color]', '<span style="color:blue;">hello world!</span>'),
        # BBCodes with syntactic errors
        ('[b]z sdf s s', '[b]z sdf s s'),
        ('[b][i]hello world![/b][/i]', '[b]<em>hello world![/b]</em>'),
        ('[b]hello [i]world![/i]', '[b]hello <em>world!</em>'),
        ('[color]test[/color]', '[color]test[/color]'),
        ('[/abcdef][/i]', '[/abcdef][/i]'),
        ('[b\n hello [i]the[/i] world![/b]', '[b<br /> hello <em>the</em> world![/b]'),
        ('[b]hello [i]the[/b] world![/i]', '[b]hello <em>the[/b] world!</em>'),
        # BBCodes with semantic errors
        ('[color=some words]test[/color]', '[color=some words]test[/color]'),
        # Unknown BBCodes
        ('[unknown][hello][/unknown]', '[unknown][hello][/unknown]'),
    )

    CUSTOM_TAGS_RENDERING_TESTS = {
        'tags': {
            'justify': {
                'args': ('justify', '[justify]{TEXT}[/justify]', '<div style="text-align:justify;">{TEXT}</div>'),
                'kwargs': {},
            },
            'spoiler': {
                'args': ('spoiler', '[spoiler]{TEXT}[/spoiler]', '<div style="margin:20px; margin-top:5px"><div class="quotetitle"><strong> </strong>   <input type="button" value="Afficher" style="width:60px;font-size:10px;margin:0px;padding:0px;" onclick="if (this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display != '') { this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display = '';        this.innerText = ''; this.value = \'Masquer\'; } else { this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display = \'none\'; this.innerText = ''; this.value = \'Afficher\'; }" /></div><div class="quotecontent"><div style="display: none;">{TEXT}</div></div></div>'),
                'kwargs': {},
            },
            'youtube': {
                'args': ('youtube', '[youtube]{TEXT}[/youtube]', '<object width="425" height="350"><param name="movie" value="http://www.youtube.com/v/{TEXT}"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/{TEXT}" type="application/x-shockwave-flash" wmode="transparent" width="425" height="350"></embed></object>'),
                'kwargs': {},
            },
            'h1': {
                'args': ('h1', '[h1={COLOR}]{TEXT}[/h1]', '<span style="border-left:6px {COLOR} solid;border-bottom:1px {COLOR} dotted;margin-left:8px;padding-left:4px;font-variant:small-caps;font-familly:Arial;font-weight:bold;font-size:150%;letter-spacing:0.2em;color:{COLOR};">{TEXT}</span><br />'),
                'kwargs': {},
            },
            'hr': {
                'args': ('hr', '[hr]', '<hr />'),
                'kwargs': {'standalone': True},
            },
            'size': {
                'args': ('size', '[size={NUMBER}]{TEXT}[/size]', '<span style="font-size:{NUMBER}px;">{TEXT}</span>'),
                'kwargs': {},
            },
        },
        'tests': (
            # BBcodes without errors
            ('[justify]hello world![/justify]', '<div style="text-align:justify;">hello world!</div>'),
            ('[spoiler]hidden![/spoiler]', '<div style="margin:20px; margin-top:5px"><div class="quotetitle"><strong> </strong>   <input type="button" value="Afficher" style="width:60px;font-size:10px;margin:0px;padding:0px;" onclick="if (this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display != '') { this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display = '';        this.innerText = ''; this.value = \'Masquer\'; } else { this.parentNode.parentNode.getElementsByTagName(\'div\')[1].getElementsByTagName(\'div\')[0].style.display = \'none\'; this.innerText = ''; this.value = \'Afficher\'; }" /></div><div class="quotecontent"><div style="display: none;">hidden!</div></div></div>'),
            ('[youtube]ztD3mRMdqSw[/youtube]', '<object width="425" height="350"><param name="movie" value="http://www.youtube.com/v/ztD3mRMdqSw"></param><param name="wmode" value="transparent"></param><embed src="http://www.youtube.com/v/ztD3mRMdqSw" type="application/x-shockwave-flash" wmode="transparent" width="425" height="350"></embed></object>'),
            ('[h1=#FFF]hello world![/h1]', '<span style="border-left:6px #FFF solid;border-bottom:1px #FFF dotted;margin-left:8px;padding-left:4px;font-variant:small-caps;font-familly:Arial;font-weight:bold;font-size:150%;letter-spacing:0.2em;color:#FFF;">hello world!</span><br />'),
            ('[hr]', '<hr />'),
            ('[size=24]hello world![/size]', '<span style="font-size:24px;">hello world!</span>'),
            # BBCodes with syntactic errors
            # BBCodes with semantic errors
            ('[size=]hello world![/size]', '[size]hello world![/size]'),
            ('[size=hello]hello world![/size]', '[size=hello]hello world![/size]'),
        )
    }

    def setUp(self):
        self.parser = BBCodeParser()

    def test_default_tags_rendering(self):
        # Run & check
        for bbcodes_text, expected_html_text in self.DEFAULT_TAGS_RENDERING_TESTS:
            result = self.parser.render(bbcodes_text)
            self.assertEqual(result, expected_html_text)

    def test_custom_tags_rendering(self):
        # Setup
        for _, tag_def in self.CUSTOM_TAGS_RENDERING_TESTS['tags'].items():
            self.parser.add_default_renderer(*tag_def['args'], **tag_def['kwargs'])
        # Run & check
        for bbcodes_text, expected_html_text in self.CUSTOM_TAGS_RENDERING_TESTS['tests']:
            result = self.parser.render(bbcodes_text)
            self.assertEqual(result, expected_html_text)
