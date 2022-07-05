
    $('#imagetag').click(function(){
      $('#upload').click();
    });

    $('#change').click(function(){
      $('#upload').click();
    });

    $('#attachement').click(function(){
      $('#upload-file').click();
      $(".fileDisplay").css("display", "block");
    });

    $(function(){
      $('#upload').change(function(){
        var input = this;
        var url = $(this).val();
        var ext = url.substring(url.lastIndexOf('.') + 1).toLowerCase();
        if (input.files && input.files[0]&& (ext == "gif" || ext == "png" || ext == "jpeg" || ext == "jpg")) 
        {
            var reader = new FileReader();

            reader.onload = function (e) {
              $('#imagetag').attr('src', e.target.result);
            }
          reader.readAsDataURL(input.files[0]);
        }
        else
        {
          $('#imagetag').attr('src', '/static/images/150x150.png');
        }
      });

    });

    $(function(){
      $('#upload-file').change(function(){
        var input = this;
        var url = $(this).val();
        var ext = url.substring(url.lastIndexOf('.') + 1).toLowerCase();
        if (input.files && input.files[0]&& (ext == "gif" || ext == "png" || ext == "jpeg" || ext == "jpg")) 
        {
            var reader = new FileReader();

            reader.onload = function (e) {
              $('#imageDisplay').attr('src', e.target.result);
            }
          reader.readAsDataURL(input.files[0]);
        }
        else
        {
          $('#imageDisplay').attr('src', '/static/images/150x150.png');
        }
      });

    });
