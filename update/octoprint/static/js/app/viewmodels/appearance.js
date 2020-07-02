$(function() {
    function AppearanceViewModel(parameters) {
        var self = this;

        self.name = parameters[0].appearance_name;
        self.color = parameters[0].appearance_color;
        self.colorTransparent = parameters[0].appearance_colorTransparent;

        self.brand = ko.pureComputed(function() {
            if (self.name())
                return gettext("3DTALK") + ": " + self.name();
            else
                return gettext("3DTALK");
        });

        self.title = ko.pureComputed(function() {
            if (self.name())
                return self.name() + " [" + gettext("3DTALK") + "]";
            else
                return gettext("3DTALK");
        });
    }

    OCTOPRINT_VIEWMODELS.push([
        AppearanceViewModel,
        ["settingsViewModel"],
        "head"
    ]);
});
