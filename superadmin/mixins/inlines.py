"""Mixins for formsets"""

# Django
from django.shortcuts import redirect


class Inlines:
    inlines = []

    def __init__(self, inline_classes, **kwargs):
        self.data = kwargs
        self.inlines = list(map(self.create, inline_classes))

    def create(self, inline_class):
        related_initial = None
        if "initial" in self.data and "related_initial" in self.data["initial"]:
            related_initial = self.data.get("initial").get("related_initial")
        self.data["initial"] = (
            related_initial.get(inline_class.model, []) if related_initial else []
        )
        inline = inline_class(**self.data)
        inline.extra += len(self.data["initial"])
        inline.headers = [
            field.label
            for field in inline.empty_form.visible_fields()
            if field.name in inline_class.form.Meta.fields
        ]
        return inline

    def is_valid(self):
        return all([inline.is_valid() for inline in self.inlines])

    def __iter__(self):
        for inline in self.inlines:
            yield inline


class InlinesMixin:
    """Class for add multiple inlines in form"""

    inlines = list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inlines = self.get_inlines()
        if isinstance(self.inlines, dict):
            for key, inline_class in self.inlines.items():
                inline = list(filter(lambda il: isinstance(il, inline_class), inlines))[
                    0
                ]
                inlines = list(filter(lambda il: not il == inline, inlines))
                context.update({key: inline})
        else:
            context.update({inline.prefix: inline for inline in inlines})
        context["inlines"] = inlines
        return context

    def get_inlines(self):
        """Method to get all formsets"""
        kwargs = self.get_form_kwargs()
        inline_classes = (
            self.inlines
            if isinstance(self.inlines, (list, tuple))
            else self.inlines.values()
        )
        inlines = Inlines(inline_classes, **kwargs)
        return inlines

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.action == "update" else None
        form = self.get_form()
        inlines = self.get_inlines()
        form.inlines = inlines
        if form.is_valid() and inlines.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        for inline in form.inlines:
            inline.instance = self.object
            inline.save()
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        for inline in form.inlines:
            for error in inline.errors:
                form.errors.update(error)
        return super().form_invalid(form)
