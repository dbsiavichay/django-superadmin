"""Mixins for formsets"""

# Django
from django.shortcuts import redirect


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

    def form_valid(self, form):
        inlines = self.get_inlines()
        valid_inlines = all(inline.is_valid() for inline in inlines)
        if valid_inlines:
            self.object = form.save()
            for inline in inlines:
                inline.instance = self.object
                inline.save()
        else:
            for inline in inlines:
                for error in inline.errors:
                    form.errors.update(error)
            return self.form_invalid(form)
        return redirect(self.get_success_url())

    def get_inlines(self):
        """Method to get all formsets"""
        kwargs = self.get_form_kwargs()
        related_initial = None
        if "initial" in kwargs and "related_initial" in kwargs["initial"]:
            related_initial = kwargs.get("initial").get("related_initial")

        def create(inline_class):
            if related_initial:
                kwargs["initial"] = related_initial.get(inline_class.model, [])
            else:
                kwargs["initial"] = []
            inline = inline_class(**kwargs)
            inline.extra += len(kwargs["initial"])
            inline.headers = [
                field.label
                for field in inline.empty_form.visible_fields()
                if field.name in inline_class.form.Meta.fields
            ]
            return inline

        inline_list = (
            self.inlines
            if isinstance(self.inlines, (list, tuple))
            else self.inlines.values()
        )
        inlines = list(map(create, inline_list))
        return inlines
