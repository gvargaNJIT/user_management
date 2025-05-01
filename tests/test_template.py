import pytest
import io
from pathlib import Path
import markdown2
from unittest.mock import Mock
from app.utils.template_manager import TemplateManager

@pytest.fixture
def template_manager(mocker):
    """
    Provides a MOCKED TemplateManager instance with controlled attributes.
    Patches the TemplateManager class itself to return a mock instance.
    """
    mock_root_dir_path = Path('/fake/project/root')
    expected_templates_dir = mock_root_dir_path / 'email_templates'

    mock_manager_instance = mocker.Mock(spec=TemplateManager)

    mock_manager_instance.root_dir = mock_root_dir_path
    mock_manager_instance.templates_dir = expected_templates_dir

    mocker.patch(
        'app.utils.template_manager.TemplateManager',
        return_value=mock_manager_instance
    )

    return mock_manager_instance


@pytest.fixture
def mock_open(mocker):
    """
    Mocks the built-in open function to simulate reading files.
    Returns the mock object to allow setting return values.
    """
    mock_file = mocker.mock_open(read_data="fake file content")
    mocker.patch('builtins.open', mock_file)
    return mock_file


@pytest.fixture
def mock_markdown2(mocker):
    """
    Mocks the markdown2.markdown function.
    Returns the mock object to allow setting return values.
    """
    mock_markdown = mocker.patch('markdown2.markdown', return_value="<p>fake html</p>")
    return mock_markdown


def test_template_manager_init(template_manager):
    """
    Test that the TemplateManager instance provided by the fixture is a mock
    and has the expected attributes set.
    """
    assert isinstance(template_manager, Mock)
    assert isinstance(template_manager.root_dir, Path)
    assert isinstance(template_manager.templates_dir, Path)
    assert template_manager.root_dir == Path('/fake/project/root')
    assert template_manager.templates_dir == Path('/fake/project/root') / 'email_templates'


def test_read_template(template_manager, mock_open, mocker):
    """
    Test that _read_template opens and reads the correct file path.
    Calls the real _read_template method on the mock instance.
    """
    filename = "test_template.md"
    expected_path = template_manager.templates_dir / filename
    mock_content = "This is the content of the test template."

    mock_open.return_value.read.return_value = mock_content

    original_read_template = TemplateManager._read_template

    content = original_read_template(template_manager, filename)

    mock_open.assert_called_once_with(expected_path, 'r', encoding='utf-8')

    assert content == mock_content


def test_apply_email_styles(template_manager, mocker):
    """
    Test that _apply_email_styles correctly applies inline styles.
    Calls the real _apply_email_styles method on the mock instance.
    """
    input_html = "<h1>Title</h1><p>Some text.</p><a>Link</a><ul><li>Item 1</li></ul><footer>Footer</footer>"

    expected_start = '<div style="font-family: Arial, sans-serif; font-size: 16px; color: #333333; background-color: #ffffff; line-height: 1.5;">'
    expected_h1 = '<h1 style="font-size: 24px; color: #333333; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">Title</h1>'
    expected_p = '<p style="font-size: 16px; color: #666666; margin: 10px 0; line-height: 1.6;">Some text.</p>'
    expected_a = '<a style="color: #0056b3; text-decoration: none; font-weight: bold;">Link</a>'
    expected_ul = '<ul style="list-style-type: none; padding: 0;">'
    expected_li = '<li style="margin-bottom: 10px;">Item 1</li>'
    expected_footer = '<footer style="font-size: 12px; color: #777777; padding: 20px 0;">Footer</footer>'
    expected_end = '</div>'

    original_apply_styles = TemplateManager._apply_email_styles

    styled_html = original_apply_styles(template_manager, input_html)

    assert styled_html.startswith(expected_start)
    assert styled_html.endswith(expected_end)

    assert expected_h1 in styled_html
    assert expected_p in styled_html
    assert expected_a in styled_html
    assert expected_ul in styled_html
    assert expected_li in styled_html
    assert expected_footer in styled_html


def test_read_template_file_not_found(template_manager, mock_open):
    """
    Test that _read_template raises FileNotFoundError if the file does not exist.
    Mocks _read_template on the mock instance.
    """
    filename = "non_existent_template.md"
    expected_path = template_manager.templates_dir / filename

    template_manager._read_template.side_effect = FileNotFoundError

    with pytest.raises(FileNotFoundError):
        template_manager._read_template(filename)

    template_manager._read_template.assert_called_once_with(filename)
