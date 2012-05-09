String.prototype.applyformat = function(data) {
	new_str = this;
	$.each(data, function(key, val) {
		new_str = new_str.replace("$" + key, val)
	});
	return new_str;
};
String.prototype.startswith = function(prefix) {
    return this.indexOf(prefix) === 0;
}

var templates = new Array();
templates["menu"] = '<a href="$url"><li>$text</li></a>';
templates["artist"] = '$name';

function sizecontents() {
	var content_height = $(window).height()-$('#header').height()-$('#footer').height();
	$('#main').height(content_height);
}
$(window).load(sizecontents);
$(window).resize(sizecontents);

function make_menu(element,menu) {
	var menu_element = $("<ul class=\"menu\"></ul>").insertAfter(element);
	element.data("menu",menu_element);
	menu_element.hide();
	var menu_item_element;
	for(menu_item in menu) {
		menu_item_element = $(templates["menu"].applyformat(menu[menu_item]));
		menu_item_element.appendTo(menu_element)
		menu_item_element.data("url",menu[menu_item]["url"]);
		menu_item_element.click(function () {menu_click($(this));});
		menu_item_element.data("state",0);
	}
	menu_element.slideDown();
}

function menu_click(element) {
	if(element.data("state") == 0) {
		var url = "/media_browser/ajax/" + element.data("url");
		url = url.replace("#/","");
		var content_html;
		console.log("Getting: "+url);
		$.getJSON(url, function(data) {
			if("menu" in data) {
				make_menu(element,data["menu"]);
			}
			/* if("template" in data) {
				content_html = templates[data["template"]];
				if("content" in data)
					content_html = content_html.applyformat(data["content"]);
				$(element).after("<div class=\"content\">" + content_html + "</div>");
			} */
		}).error(function(jqXHR, textStatus, errorThrown) { alert(textStatus + ": " + errorThrown); });

		element.data("state",2);
		return;
	}
	if(element.data("state") == 2) {
		element.data("menu").slideDown();
		element.data("state",1);
		console.log("Expanding",element.attr("href"));
		return;
	}
	if(element.data("state") == 1) {
		element.data("menu").slideUp();
		element.data("state",2);
		console.log("Contracting",element.attr("href"));
		return;
	}
}


$(window).load(function () {
	var root;
	root = $("#root");
	root.data("url","");
	root.data("state",0);
	menu_click(root);
});
