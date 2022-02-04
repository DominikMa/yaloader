def test_load_file(config_loader, AConfig, tmp_path):
    config_file_path = tmp_path.joinpath('config.yaml')
    config_file_path.write_text(
        """
        - !A {attribute: 1}
        """
    )
    config_loader.load_file(config_file_path)

    config = config_loader.construct_from_string('!A {}')

    assert config == AConfig(attribute=1)


def test_load_directory_with_yaml_files(config_loader, AConfig, tmp_path):
    config_file_path = tmp_path.joinpath('config.yaml')
    config_file_path.write_text(
        """
        - !A {attribute: 1}
        """
    )
    config_loader.load_directory(tmp_path)

    config = config_loader.construct_from_string('!A {}')

    assert config == AConfig(attribute=1)
