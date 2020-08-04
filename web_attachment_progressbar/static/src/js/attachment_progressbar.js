odoo.define('web_attachment_progressbar.composer.Basic', function (require) {
"use strict";

var emojis = require('mail.emojis');
var MentionManager = require('mail.composer.MentionManager');
var DocumentViewer = require('mail.DocumentViewer');
var utils = require('web.utils');

var config = require('web.config');
var core = require('web.core');
var data = require('web.data');
var dom = require('web.dom');
var session = require('web.session');
var Widget = require('web.Widget');

var QWeb = core.qweb;

var BasicComposer = require('mail.composer.Basic');


	BasicComposer.include({
		
		_onAttachmentChange: function (ev) {
		
			var self = this;
	        var files = ev.target.files;
	        var attachments = this.get('attachment_ids');
			var form_xhr;
			
	        _.each(files, function (file){
	            var attachment = _.findWhere(attachments, {name: file.name});
	            // if the files already exits, delete the file before upload
	            if (attachment){
	                self._attachmentDataSet.unlink([attachment.id]);
	                attachments = _.without(attachments, attachment);
	            }
	        });
	        
	        var $form = this.$('form.o_form_binary_form');
	        
	        $form.on('submit', function(e){
                e.preventDefault();
                console.log("Evt--------",e)
                form_xhr  =  $.ajax({
                    xhr: function() {
                        var xhr = new window.XMLHttpRequest();
                        xhr.upload.addEventListener("progress", function(evt) {
                        	
                            if (evt.lengthComputable) {
                                var percentComplete = parseInt((evt.loaded / evt.total) * 100);
                                $(".progress-bar-div").width(percentComplete + '%');
                                $(".progress-bar-div").html(percentComplete+'%');
                            }
                        }, false);
                        return xhr;
                    },
                    type: 'POST',
                    url: $form.attr("action"),
                    data: new FormData(this),
                    contentType: false,
                    cache: false,
                    processData:false,
                    beforeSend: function(){
                    	$('#uploadStatus').hide();
                    	$(".progress-div").show();
                    	$('.cancel_upload').show();
                        $(".progress-bar-div").width('0%');
                        $(".progress-bar-div").html('0%');
//                        $('#uploadStatus').html('<img src="images/loading.gif"/>');
                    },
                    error:function(){
                        $('#uploadStatus').html('<p style="color:#EA4335;">File upload failed, please try again.</p>');
                    },
                    success: function(result){
                    	var $el = $(result);
                        $.globalEval($el.contents().text());
                        if(result){
                        	$form.unbind('submit');
                            $('#uploadStatus').html('<p style="color:#28A74B;">File has uploaded successfully!</p>');
                        }else{
                            $('#uploadStatus').html('<p style="color:#EA4335;">Please select a valid file to upload.</p>');
                        }
                        $('#uploadStatus').show();
                        $(".progress-div").hide();
                        $('.cancel_upload').hide();
                        $(".progress-bar-div").width('0%');
                        $(".progress-bar-div").html('0%');
                    }
                });
            });
	        
	        $('.cancel_upload').click(function (e) {
        	    console.log("Cancle Upload========",e)
        		if (form_xhr) {
        	        $('#uploadStatus').html('<p style="color:#EA4335;">File Upload Cancelled!.</p>');
        	        $('#uploadStatus').show();
        	        $(".progress-div").hide();
                    $(".progress-bar-div").width('0%');
                    $(".progress-bar-div").html('0%');
                    $('.o_attachment_editable.o_attachment_uploading').remove()
                    self._$attachmentButton.prop('disabled', false);
                    var attachments = self.get('attachment_ids');
                    var new_attachments = []
                    _.each(attachments,function(key){
                    	if(key.id != 0) {
                    		new_attachments.push(key)
                    	}
                    })
                    self.set('attachment_ids',new_attachments);
                    $form.unbind('submit');
                    $(this).unbind('click');
                    form_xhr.abort();  
                    form_xhr = null;
                    $('.cancel_upload').hide();
        	    }
        	    return false;
        	});
	        
	        $form.submit()
	        this._$attachmentButton.prop('disabled', true);
	        var uploadAttachments = _.map(files, function (file){
	            return {
	                id: 0,
	                name: file.name,
	                filename: file.name,
	                url: '',
	                upload: true,
	                mimetype: '',
	            };
	        });
	        attachments = attachments.concat(uploadAttachments);
	        this.set('attachment_ids', attachments);
	        ev.target.value = "";
		},
	});



})