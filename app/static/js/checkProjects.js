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
                        $('#teamSelectDiv').append(`<p class="lead">${response.message}</p>`);
                        break;
                    case 'success':
                        $('.bootstrap-select > .dropdown-toggle').css('background-color', originalDropdownSelectBackgroundColor);
                        $('form').append('<div class="row justify-content-center" id="teamSelectDiv"></div>')

                        $('#teamSelectDiv').empty();
                        $('#submitButtonDiv').empty();
                        $('#teamSelectDiv').append('<select title="Выберите команду" data-width="500px" data-style="btn-primary" id="teamSelect" class="selectpicker show-tick"></select>');

                        let teams = response.data.teams;

                        teams.filter(team => !team.isFull).forEach(function (team) {
                            $('#teamSelect').append(`<option>${team.name} (свободных мест: ${team.emptySlots.toString()})</option>`);
                        });

                        $('.selectpicker').selectpicker();
                        $('.card-footer').empty()
                        $('.card-footer').append('<button type="submit" id="submit" class="btn btn-lg btn-success"> Записаться </button>');

                        break;
                }
            })
            .fail(function (data) {
                console.error(data);
            });
    });

    $(document).on('click', '#submit', function (event) {
        event.preventDefault();

        if (!$(document).find('#teamSelect') || $('#teamSelect').val() === 'default') {
            return;
        }

        let selectedProjectDocumentId = $('#projectSelect').find(':selected').data('documentId');
        let data = {
            name: $('#fullName').text(),
            group: $('#group').text(),
            team: $('#teamSelect').val()
        };

        $.ajax(`/api/projects/${selectedProjectDocumentId }/join`, {
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data)
        }).done(function (response) {
            let data = response.data;
            switch (response.status) {
                case 'success':
                    $.ajax('/success')
                    window.location = `/success?team_number=${data.teamNumber}&cell_index=${data.cellIndex}&project_name=${data.projectName}`
                case 'error':

            }

        }).fail(function (resp) {
            console.error(resp);
        });
    });
});