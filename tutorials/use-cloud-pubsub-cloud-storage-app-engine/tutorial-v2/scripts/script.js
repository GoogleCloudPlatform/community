var modal = document.getElementById('myModal');
var img = document.getElementById('{{thumbnail_reference.thumbnail_name}}');
var modalImg = document.getElementById('img01');
var captionText = document.getElementById("caption");
img.onclick = function(){
  modal.style.display = "block";
  modalImg.src = '{{thumbnail_reference.original_photo}}';
  captionText.innerHTML = this.alt;
}

var span = document.getElementsByClassName("close")[0];
span.onclick = function() {
  modal.style.display = "none";
}

