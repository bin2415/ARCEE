#   Domato - main generator script
#   -------------------------------
#
#   Written and maintained by Ivan Fratric <ifratric@google.com>
#
#   Copyright 2017 Google Inc. All Rights Reserved.
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from __future__ import print_function
import os
import re
import random
import sys
import logging
import string
import subprocess

from grammar import Grammar


logging.basicConfig(format = '%(asctime)-15s %(levelname)s:%(message)s', level = logging.INFO)

_N_MAIN_LINES = 1000
_N_EVENTHANDLER_LINES = 500

_N_ADDITIONAL_HTMLVARS = 5

# A map from tag name to corresponding type for HTML tags
_HTML_TYPES = {
    'a': 'HTMLAnchorElement',
    'abbr': 'HTMLUnknownElement',
    'acronym': 'HTMLUnknownElement',
    'address': 'HTMLUnknownElement',
    'applet': 'HTMLUnknownElement',
    'area': 'HTMLAreaElement',
    'article': 'HTMLUnknownElement',
    'aside': 'HTMLUnknownElement',
    'audio': 'HTMLAudioElement',
    'b': 'HTMLUnknownElement',
    'base': 'HTMLBaseElement',
    'basefont': 'HTMLUnknownElement',
    'bdi': 'HTMLUnknownElement',
    'bdo': 'HTMLUnknownElement',
    'bgsound': 'HTMLUnknownElement',
    'big': 'HTMLUnknownElement',
    'blockquote': 'HTMLUnknownElement',
    'br': 'HTMLBRElement',
    'button': 'HTMLButtonElement',
    'canvas': 'HTMLCanvasElement',
    'caption': 'HTMLTableCaptionElement',
    'center': 'HTMLUnknownElement',
    'cite': 'HTMLUnknownElement',
    'code': 'HTMLUnknownElement',
    'col': 'HTMLTableColElement',
    'colgroup': 'HTMLUnknownElement',
    'command': 'HTMLUnknownElement',
    'content': 'HTMLContentElement',
    'data': 'HTMLDataElement',
    'datalist': 'HTMLDataListElement',
    'dd': 'HTMLUnknownElement',
    'del': 'HTMLModElement',
    'details': 'HTMLDetailsElement',
    'dfn': 'HTMLUnknownElement',
    'dialog': 'HTMLDialogElement',
    'dir': 'HTMLDirectoryElement',
    'div': 'HTMLDivElement',
    'dl': 'HTMLDListElement',
    'dt': 'HTMLUnknownElement',
    'em': 'HTMLUnknownElement',
    'embed': 'HTMLEmbedElement',
    'fieldset': 'HTMLFieldSetElement',
    'figcaption': 'HTMLUnknownElement',
    'figure': 'HTMLUnknownElement',
    'font': 'HTMLFontElement',
    'footer': 'HTMLUnknownElement',
    'form': 'HTMLFormElement',
    'frame': 'HTMLFrameElement',
    'frameset': 'HTMLFrameSetElement',
    'h1': 'HTMLHeadingElement',
    'h2': 'HTMLHeadingElement',
    'h3': 'HTMLHeadingElement',
    'h4': 'HTMLHeadingElement',
    'h5': 'HTMLHeadingElement',
    'h6': 'HTMLHeadingElement',
    'header': 'HTMLUnknownElement',
    'hgroup': 'HTMLUnknownElement',
    'hr': 'HTMLHRElement',
    'i': 'HTMLUnknownElement',
    'iframe': 'HTMLIFrameElement',
    'image': 'HTMLImageElement',
    'img': 'HTMLImageElement',
    'input': 'HTMLInputElement',
    'ins': 'HTMLModElement',
    'isindex': 'HTMLUnknownElement',
    'kbd': 'HTMLUnknownElement',
    'keygen': 'HTMLKeygenElement',
    'label': 'HTMLLabelElement',
    'layer': 'HTMLUnknownElement',
    'legend': 'HTMLLegendElement',
    'li': 'HTMLLIElement',
    'link': 'HTMLLinkElement',
    'listing': 'HTMLUnknownElement',
    'main': 'HTMLUnknownElement',
    'map': 'HTMLMapElement',
    'mark': 'HTMLUnknownElement',
    'marquee': 'HTMLMarqueeElement',
    'menu': 'HTMLMenuElement',
    'menuitem': 'HTMLMenuItemElement',
    'meta': 'HTMLMetaElement',
    'meter': 'HTMLMeterElement',
    'nav': 'HTMLUnknownElement',
    'nobr': 'HTMLUnknownElement',
    'noembed': 'HTMLUnknownElement',
    'noframes': 'HTMLUnknownElement',
    'nolayer': 'HTMLUnknownElement',
    'noscript': 'HTMLUnknownElement',
    'object': 'HTMLObjectElement',
    'ol': 'HTMLOListElement',
    'optgroup': 'HTMLOptGroupElement',
    'option': 'HTMLOptionElement',
    'output': 'HTMLOutputElement',
    'p': 'HTMLParagraphElement',
    'param': 'HTMLParamElement',
    'picture': 'HTMLPictureElement',
    'plaintext': 'HTMLUnknownElement',
    'pre': 'HTMLPreElement',
    'progress': 'HTMLProgressElement',
    'q': 'HTMLQuoteElement',
    'rp': 'HTMLUnknownElement',
    'rt': 'HTMLUnknownElement',
    'ruby': 'HTMLUnknownElement',
    's': 'HTMLUnknownElement',
    'samp': 'HTMLUnknownElement',
    'section': 'HTMLUnknownElement',
    'select': 'HTMLSelectElement',
    'shadow': 'HTMLShadowElement',
    'small': 'HTMLUnknownElement',
    'source': 'HTMLSourceElement',
    'span': 'HTMLSpanElement',
    'strike': 'HTMLUnknownElement',
    'strong': 'HTMLUnknownElement',
    'style': 'HTMLStyleElement',
    'sub': 'HTMLUnknownElement',
    'summary': 'HTMLUnknownElement',
    'sup': 'HTMLUnknownElement',
    'table': 'HTMLTableElement',
    'tbody': 'HTMLTableSectionElement',
    'td': 'HTMLUnknownElement',
    'template': 'HTMLTemplateElement',
    'textarea': 'HTMLTextAreaElement',
    'tfoot': 'HTMLTableSectionElement',
    'th': 'HTMLTableCellElement',
    'thead': 'HTMLTableSectionElement',
    'time': 'HTMLTimeElement',
    'title': 'HTMLTitleElement',
    'tr': 'HTMLTableRowElement',
    'track': 'HTMLTrackElement',
    'tt': 'HTMLUnknownElement',
    'u': 'HTMLUnknownElement',
    'ul': 'HTMLUListElement',
    'var': 'HTMLUnknownElement',
    'video': 'HTMLVideoElement',
    'wbr': 'HTMLUnknownElement',
    'xmp': 'HTMLUnknownElement'
}

# A map from tag name to corresponding type for SVG tags
_SVG_TYPES = {
    'a': 'SVGAElement',
    'altGlyph': 'SVGElement',
    'altGlyphDef': 'SVGElement',
    'altGlyphItem': 'SVGElement',
    'animate': 'SVGAnimateElement',
    'animateColor': 'SVGElement',
    'animateMotion': 'SVGAnimateMotionElement',
    'animateTransform': 'SVGAnimateTransformElement',
    'circle': 'SVGCircleElement',
    'clipPath': 'SVGClipPathElement',
    'color-profile': 'SVGElement',
    'cursor': 'SVGCursorElement',
    'defs': 'SVGDefsElement',
    'desc': 'SVGDescElement',
    'discard': 'SVGDiscardElement',
    'ellipse': 'SVGEllipseElement',
    'feBlend': 'SVGFEBlendElement',
    'feColorMatrix': 'SVGFEColorMatrixElement',
    'feComponentTransfer': 'SVGFEComponentTransferElement',
    'feComposite': 'SVGFECompositeElement',
    'feConvolveMatrix': 'SVGFEConvolveMatrixElement',
    'feDiffuseLighting': 'SVGFEDiffuseLightingElement',
    'feDisplacementMap': 'SVGFEDisplacementMapElement',
    'feDistantLight': 'SVGFEDistantLightElement',
    'feDropShadow': 'SVGFEDropShadowElement',
    'feFlood': 'SVGFEFloodElement',
    'feFuncA': 'SVGFEFuncAElement',
    'feFuncB': 'SVGFEFuncBElement',
    'feFuncG': 'SVGFEFuncGElement',
    'feFuncR': 'SVGFEFuncRElement',
    'feGaussianBlur': 'SVGFEGaussianBlurElement',
    'feImage': 'SVGFEImageElement',
    'feMerge': 'SVGFEMergeElement',
    'feMergeNode': 'SVGFEMergeNodeElement',
    'feMorphology': 'SVGFEMorphologyElement',
    'feOffset': 'SVGFEOffsetElement',
    'fePointLight': 'SVGFEPointLightElement',
    'feSpecularLighting': 'SVGFESpecularLightingElement',
    'feSpotLight': 'SVGFESpotLightElement',
    'feTile': 'SVGFETileElement',
    'feTurbulence': 'SVGFETurbulenceElement',
    'filter': 'SVGFilterElement',
    'font': 'SVGElement',
    'font-face': 'SVGElement',
    'font-face-format': 'SVGElement',
    'font-face-name': 'SVGElement',
    'font-face-src': 'SVGElement',
    'font-face-uri': 'SVGElement',
    'foreignObject': 'SVGForeignObjectElement',
    'g': 'SVGGElement',
    'glyph': 'SVGElement',
    'glyphRef': 'SVGElement',
    'hatch': 'SVGElement',
    'hatchpath': 'SVGElement',
    'hkern': 'SVGElement',
    'image': 'SVGImageElement',
    'line': 'SVGLineElement',
    'linearGradient': 'SVGLinearGradientElement',
    'marker': 'SVGMarkerElement',
    'mask': 'SVGMaskElement',
    'mesh': 'SVGElement',
    'meshgradient': 'SVGElement',
    'meshpatch': 'SVGElement',
    'meshrow': 'SVGElement',
    'metadata': 'SVGMetadataElement',
    'missing-glyph': 'SVGElement',
    'mpath': 'SVGMPathElement',
    'path': 'SVGPathElement',
    'pattern': 'SVGPatternElement',
    'polygon': 'SVGPolygonElement',
    'polyline': 'SVGPolylineElement',
    'radialGradient': 'SVGRadialGradientElement',
    'rect': 'SVGRectElement',
    'set': 'SVGSetElement',
    'svg': 'SVGSVGElement',
    'solidcolor': 'SVGElement',
    'stop': 'SVGStopElement',
    'switch': 'SVGSwitchElement',
    'symbol': 'SVGSymbolElement',
    'text': 'SVGTextElement',
    'textPath': 'SVGTextPathElement',
    'title': 'SVGTitleElement',
    'tref': 'SVGElement',
    'tspan': 'SVGTSpanElement',
    'unknown': 'SVGElement',
    'use': 'SVGUseElement',
    'view': 'SVGViewElement',
    'vkern': 'SVGElement'
}

def get_random_string(length):
    '''
    generate random string with specific length

    Args:
        length

    Returns:
        random string
    '''
    letters = string.ascii_lowercase
    result_str = ''.join((random.choice(letters) for i in range(length)))
    return result_str

def check_binary(binary):
    '''
    check if binary exists

    Args:
        binary: binary

    Returns:
        True if the binary exists
    '''
    c_output = subprocess.run(['which', binary], stdout = subprocess.PIPE)

    if os.path.exists(c_output.stdout.strip()):
        return True
    return False

def get_right_index(chrome_dir):
    cur_idx = 0
    while True:
        cur_output = 'id:%06d,domato_deepfuzz' % cur_idx

        if not os.path.exists(os.path.join(chrome_dir, cur_output)):
            break
        cur_idx += 1
    return cur_idx

def generate_html_elements(ctx, n):
    for i in range(n):
        tag = random.choice(list(_HTML_TYPES))
        tagtype = _HTML_TYPES[tag]
        ctx['htmlvarctr'] += 1
        varname = 'htmlvar%05d' % ctx['htmlvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': tagtype})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + tagtype + '} */ var ' + varname + ' = document.createElement(\"' + tag + '\"); //' + tagtype + '\n'


def add_html_ids(matchobj, ctx):
    tagname = matchobj.group(0)[1:-1]
    if tagname in _HTML_TYPES:
        ctx['htmlvarctr'] += 1
        varname = 'htmlvar%05d' % ctx['htmlvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': _HTML_TYPES[tagname]})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + _HTML_TYPES[tagname] + '} */ var ' + varname + ' = document.getElementById(\"' + varname + '\"); //' + _HTML_TYPES[tagname] + '\n'
        return matchobj.group(0) + 'id=\"' + varname + '\" '
    elif tagname in _SVG_TYPES:
        ctx['svgvarctr'] += 1
        varname = 'svgvar%05d' % ctx['svgvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': _SVG_TYPES[tagname]})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + _SVG_TYPES[tagname] + '} */ var ' + varname + ' = document.getElementById(\"' + varname + '\"); //' + _SVG_TYPES[tagname] + '\n'
        return matchobj.group(0) + 'id=\"' + varname + '\" '
    else:
        return matchobj.group(0)


def generate_function_body(jsgrammar, htmlctx, num_lines):
    js = ''
    js += 'var fuzzervars = {};\n\n'
    js += "SetVariable(fuzzervars, window, 'Window');\nSetVariable(fuzzervars, document, 'Document');\nSetVariable(fuzzervars, document.body.firstChild, 'Element');\n\n"
    js += '//beginjs\n'
    js += htmlctx['htmlvargen']
    js += jsgrammar._generate_code(num_lines, htmlctx['htmlvars'])
    js += '\n//endjs\n'
    js += 'var fuzzervars = {};\nfreememory()\n'
    return js


def check_grammar(grammar):
    """Checks if grammar has errors and if so outputs them.

    Args:
      grammar: The grammar to check.
    """

    for rule in grammar._all_rules:
        for part in rule['parts']:
            if part['type'] == 'text':
                continue
            tagname = part['tagname']
            # print tagname
            if tagname not in grammar._creators:
                print('No creators for type ' + tagname)


def generate_new_sample(template, htmlgrammar, cssgrammar, jsgrammar):
    """Parses grammar rules from string.

    Args:
      template: A template string.
      htmlgrammar: Grammar for generating HTML code.
      cssgrammar: Grammar for generating CSS code.
      jsgrammar: Grammar for generating JS code.

    Returns:
      A string containing sample data.
    """

    result = template

    #css = cssgrammar.generate_symbol('rules')
    html = htmlgrammar.generate_symbol('bodyelements')

    htmlctx = {
        'htmlvars': [],
        'htmlvarctr': 0,
        'svgvarctr': 0,
        'htmlvargen': ''
    }
    html = re.sub(
        r'<[a-zA-Z0-9_-]+ ',
        lambda match: add_html_ids(match, htmlctx),
        html
    )
    generate_html_elements(htmlctx, _N_ADDITIONAL_HTMLVARS)

    #result = result.replace('<cssfuzzer>', css)
    result = result.replace('<htmlfuzzer>', html)

    handlers = False
    '''
    while '<jsfuzzer>' in result:
        numlines = _N_MAIN_LINES
        if handlers:
            numlines = _N_EVENTHANDLER_LINES
        else:
            handlers = True
        result = result.replace(
            '<jsfuzzer>',
            generate_function_body(jsgrammar, htmlctx, numlines),
            1
        )
    '''

    return result


def generate_samples(grammar_dir, out_dir):
    """Generates a set of samples and writes them to the output files.

    Args:
      grammar_dir: directory to load grammar files from.
      outfiles: A list of output filenames.
    """

    chrome_valid_cnt = 0
    wkhtml_valid_cnt = 0

    chrome_dir = os.path.join(out_dir, 'chrome_domato')
    wkhtml_dir = os.path.join(out_dir, 'wkhtml_domato')

    f = open(os.path.join(grammar_dir, 'template.html'))
    template = f.read()
    f.close()

    htmlgrammar = Grammar()
    err = htmlgrammar.parse_from_file(os.path.join(grammar_dir, 'html.txt'))
    # CheckGrammar(htmlgrammar)
    if err > 0:
        print('There were errors parsing grammar')
        return

    cssgrammar = Grammar()
    err = cssgrammar.parse_from_file(os.path.join(grammar_dir, 'css.txt'))
    # CheckGrammar(cssgrammar)
    if err > 0:
        print('There were errors parsing grammar')
        return

    jsgrammar = Grammar()
    err = jsgrammar.parse_from_file(os.path.join(grammar_dir, 'js.txt'))
    # CheckGrammar(jsgrammar)
    if err > 0:
        print('There were errors parsing grammar')
        return

    # JS and HTML grammar need access to CSS grammar.
    # Add it as import
    htmlgrammar.add_import('cssgrammar', cssgrammar)
    jsgrammar.add_import('cssgrammar', cssgrammar)

    tmp_html_file = '/tmp/%s.html' % get_random_string(8)

    if not os.path.exists(chrome_dir):
        mk_cmd = 'mkdir -p %s' % chrome_dir
        os.system(mk_cmd)
        print(mk_cmd)
    else:
        chrome_valid_cnt = get_right_index(chrome_dir)

    if not os.path.exists(wkhtml_dir):
        mk_cmd = 'mkdir -p %s' % wkhtml_dir
        os.system(mk_cmd)
        print(mk_cmd)
    else:
        wkhtml_valid_cnt = get_right_index(wkhtml_dir)

    if not check_binary('google-chrome'):
        print('Please install google-chrome firstly!')
        exit(-1)

    if not check_binary('wkhtmltopdf'):
        print('Please install wkhtmltopdf firstly!')
        exit(-1)

    while True:
        try:
            result = generate_new_sample(template, htmlgrammar, cssgrammar,
                                         jsgrammar)

            if result is not None:
                print('Writing a sample to ' + tmp_html_file)
                try:
                    f = open(tmp_html_file, 'w')
                    f.write(result)
                    f.close()
                except IOError:
                    print('Error writing to output')
                    continue

            wkhtml_output = os.path.join(wkhtml_dir, 'id:%06d,domato_deepfuzz' % wkhtml_valid_cnt)
            chrome_output = os.path.join(chrome_dir, 'id:%06d,domato_deepfuzz' % chrome_valid_cnt)
            chrome_cmd = 'timeout 10s google-chrome --headless --disable-gpu --print-to-pdf=%s %s' % (chrome_output, tmp_html_file)
            wkhtml_cmd = 'timeout 10s wkhtmltopdf %s %s' % (tmp_html_file, wkhtml_output)

            chrome_run = subprocess.run(chrome_cmd.split(), stdout = subprocess.PIPE)
            if chrome_run.returncode == 0 or os.path.exists(chrome_output):
                print('generate chrome pdf %s' % chrome_output)
                chrome_valid_cnt += 1

            wkhtml_run = subprocess.run(wkhtml_cmd.split(), stdout = subprocess.PIPE)
            if wkhtml_run.returncode == 0 or os.path.exists(wkhtml_output):
                print('generate wkhtml pdf %s' % wkhtml_output)
                wkhtml_valid_cnt += 1

        except KeyboardInterrupt:
            os.system('rm %s' % tmp_html_file)
            print('Catch ctrl-c. Exiting...')
            exit(0)




def get_option(option_name):
    for i in range(len(sys.argv)):
        if (sys.argv[i] == option_name) and ((i + 1) < len(sys.argv)):
            return sys.argv[i + 1]
        elif sys.argv[i].startswith(option_name + '='):
            return sys.argv[i][len(option_name) + 1:]
    return None


def main():
    fuzzer_dir = os.path.dirname(__file__)

    multiple_samples = False

    for a in sys.argv:
        if a.startswith('--output_dir='):
            multiple_samples = True

    if '--output_dir' in sys.argv:
        multiple_samples = True

    if not multiple_samples:
        print('Please specify the directory of output with "--output_dir"')
        exit(-1)

    out_dir = get_option('--output_dir')

    generate_samples(fuzzer_dir, out_dir)

if __name__ == '__main__':
    main()
