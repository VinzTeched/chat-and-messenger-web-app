
    $(document).ready(function(e){
        $(".add").click(function(){
          var id=$(this).attr('id').split("-")[1];
          $.ajax({
            url:'/new-friend',
            data:'friend_id='+id,
            type: "POST",
            beforeSend: function(){
              $('#add-'+id).text('Adding');
            },
            success: function(data){
              if(data == "success"){
                $('#add-'+id).text('Added');
                $('#add-'+id).attr('class', 'btn btn-sm btn-success');
                $('#friend-result').trigger('click');
              } else{
                alert(data)
                $('#add-'+id).text('Friends');
                $('#add-'+id).attr('class', 'btn btn-sm btn-secondary');
              }
            }
        });
      });

      $(".getFriendMessage").click(function(){
        var id=$(this).attr('id').split("-")[1];
        $.ajax({
          url:'/get-message',
          data:'friend_id='+id,
          type: "POST",
          beforeSend: function(){
            $('.getFriendMessage').removeClass("active");
            $('.profile-date').addClass("text-muted");
            //$('#add-'+id).text('Adding');
          },
          success: function(data){
            $(".shownow").css("display", "block");
            $(".hidenow").css("display", "none");
            $('#findFriendName').trigger('click');
            $('#triggerLoad').trigger('click');
            $('#contact-info').trigger('click');
            $('.hana'+id).addClass("active");
            $('.dateof'+id).removeClass("text-muted");
          }
        });
      });

      $("#startNewChat").click(function () {
        $(".newchat").css("display", "block");
      });  

    });
