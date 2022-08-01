$(document).ready(function() {

  // Carousel Configs
  var banners = $('#banners')
  var f_products = $('#f-products')

  banners.owlCarousel({
    loop:true,
    margin:10,
    items: 1,
    autoplay: true,
    autoplayTimeout: 6000,
    smartSpeed: 1500,
    autoplayHoverPause: true,
  })

  f_products.owlCarousel({
    loop:false,
    nav:true,
    margin:10,
    dots:false,
    smartSpeed:1000,
    slideSpeed: 300,
    paginationSpeed: 400,
    navText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
    responsive:{
        0:{
            items:2
        },
        600:{
            items:3
        },
        1000:{
            items:5
        }
    }
  });

  f_products.on('mousewheel', '.owl-stage', function (e) {
    if (e.deltaY>0) {
      f_products.trigger('next.owl');
    } else {
      f_products.trigger('prev.owl');
    }
    e.preventDefault();

  });

  // check input field
  $('#search-submit').submit(function() {
    if ($.trim($("#searchInput").val()) === ""){
        return false;
    }
  });

  // search autocomplete
  function autocomplete(inp) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
  
    function view_suggestions(inp,arr){
      var a, b, i, val = inp.value;
      /*close any already open lists of autocompleted values*/
      closeAllLists();
      currentFocus = -1;
      /*create a DIV element that will contain the items (values):*/
      a = document.createElement("DIV");
      a.setAttribute("id", inp.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items font-family-3");
      /*append the DIV element as a child of the autocomplete container:*/
      inp.parentNode.appendChild(a);
      /*for each item in the array...*/
      for (i = 0; i < arr.length && i < 7; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        // if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        /*create a DIV element for each matching element:*/
        b = document.createElement("DIV");
        /*make the matching letters bold:*/
        b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
        b.innerHTML += arr[i].substr(val.length);
        /*insert a input field that will hold the current array item's value:*/
        b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
        /*execute a function when someone clicks on the item value (DIV element):*/
        b.addEventListener("click", function(e) {
            /*insert the value for the autocomplete text field:*/
            inp.value = this.getElementsByTagName("input")[0].value;
            /*close the list of autocompleted values,
            (or any other open lists of autocompleted values:*/
            closeAllLists();
        });
        b.addEventListener("mouseover", function(e) {
          /*insert the value for the autocomplete text field:*/
          inp.value = this.getElementsByTagName("input")[0].value;
        });
        b.addEventListener("mouseout", function(e) {
          /*insert the value for the autocomplete text field:*/
          inp.value = localStorage.orig_query;
        });
        a.appendChild(b);
        // }
      }
    }
    
    /* trigger search autocomplete request after typing (inactivity within 200ms)*/
    function debounce(callback, wait) {
      let timeout;
      return (...args) => {
          clearTimeout(timeout);
          timeout = setTimeout(function () { callback.apply(this, args); }, wait);
      };
    }
    
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener('input', debounce( () => {
      var val = inp.value.toLowerCase();
      localStorage.orig_query = val;
      words = val.split(' ')
      if (words[words.length-1]==''){
        if (words.length==1){closeAllLists();}
        return false;}
      if (!val) { closeAllLists(); return false;}
      if(window.navigator.onLine){
        $.ajax({
          type : 'POST',
          url : "/processing",
          data : {'query': val},
          success : function(response){
            view_suggestions(inp,response.autocomplete)
          }
        });
      }
    }, 200))
    
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
      var x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");
      if (e.keyCode == 40) {
        /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
        currentFocus++;
        /*and and make the current item more visible:*/
        addActive(x);
        if (x) inp.value = x[currentFocus].getElementsByTagName("input")[0].value;
      } else if (e.keyCode == 38) { //up
        /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
        currentFocus--;
        /*and and make the current item more visible:*/
        addActive(x);
        if (x) inp.value = x[currentFocus].getElementsByTagName("input")[0].value;
      } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        // e.preventDefault();
        if (currentFocus > -1) {
          /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        }
      }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
        }
      }
    }
    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
      closeAllLists(e.target);
    });
  }
  // autocomplete processing
  inp = document.getElementById("searchInput");
  autocomplete(inp)

  // dynamic active buttons
  var num = localStorage.b_active
  if (num!=0){
  $('button[value="'+num+'"]').addClass('active');
  }else{
    $('button[value="'+1+'"]').addClass('active');
  }

  // dynamic pagination buttons
  if ($('#min-page').attr("value")==="1"){
    if (!$('#prev').hasClass('disable_b')){
      $('#prev').addClass('disable_b');
    }
  }else{
    if ($('#prev').hasClass('disable_b')){
      $('#prev').removeClass('disable_b');
    }
  }
  if ($('#min-page').attr("value")===$('#max-page').attr("value")){  
    if (!$('#next').hasClass('disable_b')){
      $('#next').addClass('disable_b');
    }
  }else{
    if ($('#next').hasClass('disable_b')){
      $('#next').removeClass('disable_b');
    }
  }

  // disable some buttons when specific category is chosen
  $('#top-items').on('click',function() {
    localStorage.b_active = 3;
    localStorage.setItem('b_disable',[1,2]);
    localStorage.setItem('b_enable', 'null'); 
  });
  $('#latest-items').on('click',function() {
    localStorage.b_active = 2;
    localStorage.setItem('b_disable',[1,3]);
    localStorage.setItem('b_enable', 'null');
  });

  // re-enable when performing search
  $('.search-form').on('submit',function() {
    localStorage.b_active = 1;
    localStorage.setItem('b_enable',[1,2,3]);
  });

  // set disable buttons
  if (localStorage.getItem('b_disable') !== 'null'){
    if (localStorage.hasOwnProperty('b_disable')){
      elems = localStorage.getItem('b_disable');
      for (i=0;i<elems.length;i++){
        if (!$('button[value="'+elems[i]+'"]').hasClass('disable_b')){
          $('button[value="'+elems[i]+'"]').addClass('disable_b');
        }
      } 
    }
  }

  // set enable buttons
  if (localStorage.getItem('b_enable') !== 'null'){
    if (localStorage.hasOwnProperty('b_enable')){
      elems = localStorage.getItem('b_enable');
      for (i=0;i<elems.length;i++){
        if ($('button[value="'+elems[i]+'"]').hasClass('disable_b')){
          $('button[value="'+elems[i]+'"]').removeClass('disable_b');
        }
      }
    }
    localStorage.setItem('b_disable', 'null') 
  }
});

// shortcuts configs
shortcuts = function(e) {
  localStorage.b_active = 1
  localStorage.setItem('b_enable',[1,2,3])
  console.log(e.currentTarget.textContent)
  $.ajax({
    type : 'POST',
    url : "/shortcuts",
    data : {'query':e.currentTarget.textContent},
    success: function(response) {
      if (response.redirect) {
        window.location.href = response.redirect;
      }
    }
  });
  return false
}

// Menu Toggle
var MenuItems = document.getElementById("MenuItems");
MenuItems.style.maxHeight = "0px";

function menutoggle(){
    if(MenuItems.style.maxHeight == "0px"){
        MenuItems.style.maxHeight = "500px";
    }else{
        MenuItems.style.maxHeight = "0px";
    }
}
  
// Sort Buttons
var btnContainer = document.getElementById("sort");
var btns = btnContainer.getElementsByClassName("btn");

// loop through the buttons and add the active class to the current/clicked button
for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function() {
    var current = document.getElementsByClassName("active");

    // if there's no active class
    if (current.length > 0) {
      current[0].className = current[0].className.replace(" active", "");
      localStorage.b_active = $(this).attr("value")
    }
    this.className += " active";
  });
}