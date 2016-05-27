openerp.nh_clinical = function(instance){

    instance.web.form.SelectCreatePopup.include({
        setup_search_view: function(search_defaults) {
            var self = this;
            if(self.options.title.indexOf('Nursing Staff for new shift') > -1){
                self.options.no_create = true;
            }
            self._super(search_defaults);
        },
    })
};