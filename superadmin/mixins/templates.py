class TemplateMixin:
    def get_template_names(self):
        action = self.template_name_suffix.split("_")[-1]
        self.template_name = getattr(self.site, "%s_template_name" % action)
        return super().get_template_names()