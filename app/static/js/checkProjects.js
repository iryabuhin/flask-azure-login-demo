$(function() {
    $('.selectpicker').selectpicker();

    let originalDropdownSelectBackgroundColor = $('.bootstrap-select > .dropdown-toggle').css('background-color');

    $(document).on('change', '#projectSelect', function () {
        let selectedProjectId = $(this).find(':selected').data('documentId');
        $.getJSON(`/api/projects/${selectedProjectId}/available`, {})
            .done(function (response) {
                switch (response.status) {
                    case 'error':
                        $('.bootstrap-select > .dropdown-toggle').css('background-color', '#d9534f');

                        $('#teamSelectDiv').empty();
                        $('#teamSelectDiv').append(`<p class="lead font-weight-bold">${response.message}</p>`);
                        break;
                    case 'success':
                        $('.bootstrap-select > .dropdown-toggle').css('background-color', originalDropdownSelectBackgroundColor);

                        $('#teamSelectDiv').empty();
                        $('#submitButtonDiv').empty();
                        $('#teamSelectDiv').append('<select title="Выберите команду" data-width="500px" data-style="btn-primary" id="teamSelect" class="selectpicker show-tick"></select>');

                        let teams = response.data.teams;

                        teams.filter(team => !team.isFull).forEach(function (team) {
                            $('#teamSelect').append(`<option>${team.name} (свободных мест: ${team.emptySlots.toString()})</option>`);
                        });

                        $('.selectpicker').selectpicker();

                        $('form').append('<div id="submitButtonDiv" class="row my-3 justify-content-center"></div>');
                        $('form > .row').last().append('<button type="submit" class="btn btn-lg btn-success"> Отправить  </button>')

                        break;
                }
            })
            .fail(function (data) {
                console.error(data);
            });
    });

    $(document).on('submit', 'form', function (event) {
        event.preventDefault();

        if (!$(document).find('#teamSelect') || $('#teamSelect').val() === 'default') {
            return;
        }

        let selectedProjectDocumentId = $(this).find(':selected').data('documentId');
        let data = {
            name: $('#fullName').text(),
            group: $('#group').text(),
            team: $('#teamSelect').val()
        };

        $.ajax(`/api/projects/${selectedProjectDocumentId }/join`, {
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data)
        }).done(function (resp) {
            switch (resp.status) {
                case 'success':
                    window.location = '/#';
                case 'error':

            }

        }).fail(function (resp) {
            console.error(resp);
        })
    });
});