odoo.define('scout_stock.payment_form', function (require) {
        "use strict";

        var ajax = require('web.ajax');
        var config = require('web.config');
        var core = require('web.core');
        var dom = require('web.dom');
        var Dialog = require("web.Dialog");
        var Widget = require("web.Widget");
        var rpc = require("web.rpc");
        var _t = core._t;
        var payment_widget = require("payment.payment_form");
        
        $(document).ready(function(){ 
            
            var pay_now_button = $('button#o_payment_form_pay')
            var checked_radio_pm = $("input[type=radio][name=pm_id]:checked")
            $('input[type=radio][name=pm_id]').on('change', function() {
              var provider_cod = $(this).attr("data-provider")
              if(provider_cod == 'transfer'){
                    pay_now_button.text('Checkout')
                }else{
                    pay_now_button.text('Pay Now')
                }
            });
            if(checked_radio_pm && pay_now_button){
                checked_radio_pm = $(checked_radio_pm).attr("data-provider");
                if(checked_radio_pm == 'transfer'){
                    pay_now_button.text('Checkout')
                }else{
                    pay_now_button.text('Pay Now')
                }
            }

        });

        // $(document).ready(function(){ 
            
        //     var checked_radio_pm = false
        //     checked_radio_pm = $("input[type=radio][name=pm_id]:checked")
        //     $('input[type=radio][name=pm_id]').on('change', function() {
        //       checked_radio_pm = $(this).attr("data-acquirer-id")
        //       var provider_cod = $(this).attr("data-provider")
        //       if(checked_radio_pm){
        //             ajax.jsonRpc('/checked/cod/method','call',{'acquirer_id':checked_radio_pm})
        //             .then(function(vals){
        //                 if (vals){
        //                     window.location.reload();
        //                 }
        //             })
        //         }
        //     });
        //     if(checked_radio_pm){
        //         checked_radio_pm = $(checked_radio_pm).attr("data-acquirer-id");
        //         if(checked_radio_pm){
        //             ajax.jsonRpc('/checked/cod/method','call',{'acquirer_id':checked_radio_pm})
        //             .then(function(vals){
        //                 console.log('=======2====',vals)
        //             })
        //         }   
        //     }
        //     ajax.jsonRpc('/checked/payment/method','call',{})
        //     .then(function(data){
        //         if(data){
        //             var pay_method = $("input[type=radio][name=pm_id]")
        //             $.each(pay_method, function(key, value) {
        //                 var pay_id = $(value).attr('data-acquirer-id')
        //                 if(pay_id == data){
        //                     $(value).prop("checked", true);
        //                     ajax.jsonRpc('/checked/cod/method','call',{'acquirer_id':pay_id})
        //                     .then(function(vals){
        //                     })
        //                 }
        //             });
        //         }
        //     })
            
        // });
        
        
        payment_widget.include({
        	
        	payEvent: function (ev) {
                ev.preventDefault();
                var form = this.el;
                var checked_radio = this.$('input[type="radio"]:checked');
                var self = this;
                var button = ev.target;
                ajax.jsonRpc('/check/all_shipping_are_calculated','call',{}).then(function(val){
                	if(!val){
                        var bs_modal11 = '<div class="modal fade" id="worning_pay_button" role="dialog"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h4 class="modal-title">WARNING!</h4><button type="button" class="close" data-dismiss="modal">×</button></div><div class="modal-body">One of Shipping methods are missing. Please Choose!</div></div></div></div>'
                        $(form).append(bs_modal11)
                        $("#worning_pay_button").modal("show");
            //     		$.alert({
        				//     title: 'Warning!',
        				//     content: 'One of Shipping methods are missing.Please Choose!',
        				// });
                	}
                	else{
                		// first we check that the user has selected a payment method
                        if (checked_radio.length === 1) {
                            checked_radio = checked_radio[0];

                            // we retrieve all the input inside the acquirer form and 'serialize' them to an indexed array
                            var acquirer_id = self.getAcquirerIdFromRadio(checked_radio);
                            var acquirer_form = false;
                            if (self.isNewPaymentRadio(checked_radio)) {
                                acquirer_form = self.$('#o_payment_add_token_acq_' + acquirer_id);
                            } else {
                                acquirer_form = self.$('#o_payment_form_acq_' + acquirer_id);
                            }
                            var inputs_form = $('input', acquirer_form);
                            var ds = $('input[name="data_set"]', acquirer_form)[0];

                            // if the user is adding a new payment
                            if (self.isNewPaymentRadio(checked_radio)) {
                                if (self.options.partnerId === undefined) {
                                    console.warn('payment_form: unset partner_id when adding new token; things could go wrong');
                                }
                                var form_data = self.getFormData(inputs_form);
                                var wrong_input = false;

                                inputs_form.toArray().forEach(function (element) {
                                    //skip the check of non visible inputs
                                    if ($(element).attr('type') == 'hidden') {
                                        return true;
                                    }
                                    $(element).closest('div.form-group').removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');
                                    $(element).siblings( ".o_invalid_field" ).remove();
                                    //force check of forms validity (useful for Firefox that refill forms automatically on f5)
                                    $(element).trigger("focusout");
                                    if (element.dataset.isRequired && element.value.length === 0) {
                                            $(element).closest('div.form-group').addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid');
                                            $(element).closest('div.form-group').append('<div style="color: red" class="o_invalid_field" aria-invalid="true">' + _.str.escapeHTML("The value is invalid.") + '</div>');
                                            wrong_input = true;
                                    }
                                    else if ($(element).closest('div.form-group').hasClass('o_has_error')) {
                                        wrong_input = true;
                                        $(element).closest('div.form-group').append('<div style="color: red" class="o_invalid_field" aria-invalid="true">' + _.str.escapeHTML("The value is invalid.") + '</div>');
                                    }
                                });

                                if (wrong_input) {
                                    return;
                                }

                                self.disableButton(button);
                                var verify_validity = self.$el.find('input[name="verify_validity"]');

                                if (verify_validity.length>0) {
                                    form_data.verify_validity = verify_validity[0].value === "1";
                                }

                                // do the call to the route stored in the 'data_set' input of the acquirer form, the data must be called 'create-route'
                                return ajax.jsonRpc(ds.dataset.createRoute, 'call', form_data).then(function (data) {
                                    // if the server has returned true
                                    if (data.result) {
                                        // and it need a 3DS authentication
                                        if (data['3d_secure'] !== false) {
                                            // then we display the 3DS page to the user
                                            $("body").html(data['3d_secure']);
                                        }
                                        else {
                                            checked_radio.value = data.id; // set the radio value to the new card id
                                            form.submit();
                                            return $.Deferred();
                                        }
                                    }
                                    // if the server has returned false, we display an error
                                    else {
                                        if (data.error) {
                                            self.displayError(
                                                '',
                                                data.error);
                                        } else { // if the server doesn't provide an error message
                                            self.displayError(
                                                _t('Server Error'),
                                                _t('e.g. Your credit card details are wrong. Please verify.'));
                                        }
                                    }
                                    // here we remove the 'processing' icon from the 'add a new payment' button
                                    self.enableButton(button);
                                }).fail(function (error, event) {
                                    // if the rpc fails, pretty obvious
                                    self.enableButton(button);

                                    self.displayError(
                                        _t('Server Error'),
                                        _t("We are not able to add your payment method at the moment.") +
                                           error.data.message
                                    );
                                });
                            }
                            // if the user is going to pay with a form payment, then
                            else if (self.isFormPaymentRadio(checked_radio)) {
                                var $tx_url = self.$el.find('input[name="prepare_tx_url"]');
                                // if there's a prepare tx url set
                                if ($tx_url.length === 1) {
                                    // if the user wants to save his credit card info
                                    var form_save_token = acquirer_form.find('input[name="o_payment_form_save_token"]').prop('checked');
                                    // then we call the route to prepare the transaction
                                    return ajax.jsonRpc($tx_url[0].value, 'call', {
                                        'acquirer_id': parseInt(acquirer_id),
                                        'save_token': form_save_token,
                                        'access_token': self.options.accessToken,
                                        'success_url': self.options.successUrl,
                                        'error_url': self.options.errorUrl,
                                        'callback_method': self.options.callbackMethod,
                                        'order_id': self.options.orderId,
                                    }).then(function (result) {
                                        if (result) {
                                            // if the server sent us the html form, we create a form element
                                            var newForm = document.createElement('form');
                                            newForm.setAttribute("method", "post"); // set it to post
                                            newForm.setAttribute("provider", checked_radio.dataset.provider);
                                            newForm.hidden = true; // hide it
                                            newForm.innerHTML = result; // put the html sent by the server inside the form
                                            var action_url = $(newForm).find('input[name="data_set"]').data('actionUrl');
                                            newForm.setAttribute("action", action_url); // set the action url
                                            $(document.getElementsByTagName('body')[0]).append(newForm); // append the form to the body
                                            $(newForm).find('input[data-remove-me]').remove(); // remove all the input that should be removed
                                            if(action_url) {
                                                newForm.submit(); // and finally submit the form
                                                return $.Deferred();
                                            }
                                        }
                                        else {
                                            self.displayError(
                                                _t('Server Error'),
                                                _t("We are not able to redirect you to the payment form.")
                                            );
                                        }
                                    }).fail(function (error, event) {
                                        self.displayError(
                                            _t('Server Error'),
                                            _t("We are not able to redirect you to the payment form. ") +
                                               error.data.message
                                        );
                                    });
                                }
                                else {
                                    // we append the form to the body and send it.
                                	self.displayError(
                                        _t("Cannot set-up the payment"),
                                        _t("We're unable to process your payment.")
                                    );
                                }
                            }
                            else {  // if the user is using an old payment then we just submit the form
                            	self.disableButton(button);
                                form.submit();
                                return $.Deferred();
                            }
                        }
                        else {
                        	self.displayError(
                                _t('No payment method selected'),
                                _t('Please select a payment method.')
                            );
                        }
                	}
                })
                
            },
        		
    	})
});