# WebPyMail - IMAP python/django web mail client
# Copyright (C) 2008 Helder Guerreiro

# This file is part of WebPyMail.
#
# WebPyMail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WebPyMail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hlimap.  If not, see <http://www.gnu.org/licenses/>.

#
# Helder Guerreiro <helder@tretas.org>
#

'''
Adaptation of Django's django.template.loader_tags.py to redefine
{% extends ... %} and {% include ... %} making this tags aware of the theme
mechanics:

    For a given theme we'll contruct a template list:

    [ <theme>/<template>, <default theme>/<template>, <template> ]

The first template to be found is used.
'''

from django.conf import settings
from django.utils import six
from django.template.base import (Node, Template, TemplateSyntaxError,
                                  TextNode, Variable, token_kwargs,
                                  VariableDoesNotExist)
from django.template.library import Library
from django.template.loader import select_template

from django.template.loader_tags import BLOCK_CONTEXT_KEY
from django.template.loader_tags import BlockContext, BlockNode
from django.template.loader_tags import construct_relative_path

# Local Imports
from themesapp.shortcuts import get_theme

register = Library()

DEFAULT_THEME = getattr(settings, 'DEFAULT_THEME', 'default')


class LoaderNode(Node):
    def get_theme(self, context):
        # Get the current theme:
        try:
            request = Variable('request').resolve(context)
        except VariableDoesNotExist:
            request = None
        return get_theme(request)

    def select_template(self, template_name, context):
        theme = self.get_theme(context)
        t = select_template(['%s/%s' % (theme,  template_name,),
                             '%s/%s' % (DEFAULT_THEME, template_name),
                             template_name])
        return t.template


class ExtendsNode(LoaderNode):
    must_be_first = False
    context_key = 'extends_context'

    def __init__(self, nodelist, parent_name, template_dirs=None):
        self.nodelist = nodelist
        self.parent_name = parent_name
        self.template_dirs = template_dirs
        self.blocks = {n.name: n
                       for n in nodelist.get_nodes_by_type(BlockNode)}

    def __repr__(self):
        return '<ExtendsNode: extends %s>' % self.parent_name.token

    def find_template(self, template_name, context):
        """
        This is a wrapper around engine.find_template(). A history is kept in
        the render_context attribute between successive extends calls and
        passed as the skip argument. This enables extends to work recursively
        without extending the same template twice.
        """
        history = context.render_context.setdefault(
            self.context_key, [context.template.origin],
        )
        template, origin = context.template.engine.find_template(
            template_name, skip=history,
        )
        history.append(origin)
        return template

    def get_parent(self, context):
        parent = self.parent_name.resolve(context)
        if not parent:
            error_msg = "Invalid template name in 'extends' tag: %r." % parent
            if self.parent_name.filters or\
                    isinstance(self.parent_name.var, Variable):
                error_msg += " Got this from the '%s' variable." %\
                    self.parent_name.token
            raise TemplateSyntaxError(error_msg)
        if isinstance(parent, Template):
            # parent is a django.template.Template
            return parent
        if isinstance(getattr(parent, 'template', None), Template):
            # parent is a django.template.backends.django.Template
            return parent.template
        return self.select_template(parent, context)

    def render(self, context):
        compiled_parent = self.get_parent(context)

        if BLOCK_CONTEXT_KEY not in context.render_context:
            context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
        block_context = context.render_context[BLOCK_CONTEXT_KEY]

        # Add the block nodes from this node to the block context
        block_context.add_blocks(self.blocks)

        # If this block's parent doesn't have an extends node it is the root,
        # and its block nodes also need to be added to the block context.
        for node in compiled_parent.nodelist:
            # The ExtendsNode has to be the first non-text node.
            if not isinstance(node, TextNode):
                if not isinstance(node, ExtendsNode):
                    nodelist = compiled_parent.nodelist
                    blocks = {n.name: n for n in
                              nodelist.get_nodes_by_type(BlockNode)}
                    block_context.add_blocks(blocks)
                break

        # Call Template._render explicitly so the parser context stays
        # the same.
        return compiled_parent._render(context)


class IncludeNode(LoaderNode):
    context_key = '__include_context'

    def __init__(self, template, *args, extra_context=None, isolated_context=False, **kwargs):
        self.template = template
        self.extra_context = extra_context or {}
        self.isolated_context = isolated_context
        super().__init__(*args, **kwargs)

    def render(self, context):
        """
        Render the specified template and context. Cache the template object
        in render_context to avoid reparsing and loading when used in a for
        loop.
        """
        template = self.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, 'render', None)):
            # If not, try the cache and get_template().
            template_name = template
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = self.select_template(template_name, context)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, 'template'):
            template = template.template
        values = {
            name: var.resolve(context)
            for name, var in self.extra_context.items()
        }
        if self.isolated_context:
            return template.render(context.new(values))
        with context.push(**values):
            return template.render(context)


@register.tag('extends')
def do_extends(parser, token):
    """
    Signal that this template extends a parent template.

    This tag may be used in two ways: ``{% extends "base" %}`` (with quotes)
    uses the literal value "base" as the name of the parent template to extend,
    or ``{% extends variable %}`` uses the value of ``variable`` as either the
    name of the parent template to extend (if it evaluates to a string) or as
    the parent template itself (if it evaluates to a Template object).
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    parent_name = parser.compile_filter(bits[1])
    nodelist = parser.parse()
    if nodelist.get_nodes_by_type(ExtendsNode):
        raise TemplateSyntaxError(
            "'%s' cannot appear more than once in the same template" % bits[0])
    return ExtendsNode(nodelist, parent_name)


@register.tag('include')
def do_include(parser, token):
    """
    Loads a template and renders it with the current context. You can pass
    additional context using keyword arguments.

    Example::

        {% include "foo/some_include" %}
        {% include "foo/some_include" with bar="BAZZ!" baz="BING!" %}

    Use the ``only`` argument to exclude the current context when rendering
    the included template::

        {% include "foo/some_include" only %}
        {% include "foo/some_include" with bar="1" only %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: the name of the template to "
            "be included." % bits[0]
        )
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})
    bits[1] = construct_relative_path(parser.origin.template_name, bits[1])
    return IncludeNode(parser.compile_filter(bits[1]), extra_context=namemap,
                       isolated_context=isolated_context)
