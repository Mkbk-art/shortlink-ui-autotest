from __future__ import annotations

import pytest

from utils.test_data_factory import build_group_data


@pytest.mark.ui
class TestGroup:
    """短链分组：CRUD、选择、空名称规则与拖拽排序。"""

    def test_group_create_and_select(self, authenticated_group_page):
        group = build_group_data()
        page = authenticated_group_page
        try:
            page.create_group(group.name).select_group(group.name)
            assert page.has_group(group.name)
            assert page.is_group_selected(group.name)
        finally:
            if page.has_group(group.name):
                page.delete_group(group.name)

    def test_group_cancel_creation(self, authenticated_group_page):
        group = build_group_data()
        authenticated_group_page.cancel_create_group(group.name)
        assert not authenticated_group_page.has_group(group.name)

    def test_group_blank_name_is_allowed(self, authenticated_group_page):
        page = authenticated_group_page
        before = page.blank_group_count()
        try:
            page.create_blank_group()
            assert page.blank_group_count() == before + 1
        finally:
            if page.blank_group_count() > before:
                cleaned = page.delete_one_blank_group()
                assert cleaned, "空名称分组已创建，但 UI 清理失败"

        assert page.blank_group_count() == before

    def test_group_rename(self, authenticated_group_page, temporary_group):
        old_name = temporary_group.name
        new_group = build_group_data(prefix="ui-r")

        authenticated_group_page.rename_group(old_name, new_group.name)
        temporary_group.name = new_group.name

        assert not authenticated_group_page.has_group(old_name)
        assert authenticated_group_page.has_group(new_group.name)

    def test_group_delete(self, authenticated_group_page, temporary_group):
        authenticated_group_page.delete_group(temporary_group.name)
        temporary_group.active = False
        assert not authenticated_group_page.has_group(temporary_group.name)

    def test_group_selection_switch(self, authenticated_group_page, temporary_group_pair):
        first, second = temporary_group_pair
        page = authenticated_group_page

        page.select_group(first.name)
        assert page.is_group_selected(first.name)

        page.select_group(second.name)
        assert page.is_group_selected(second.name)
        assert not page.is_group_selected(first.name)

    @pytest.mark.regression
    def test_group_drag_sort(self, authenticated_group_page, temporary_group_pair):
        first, second = temporary_group_pair
        page = authenticated_group_page

        before, after = page.drag_group_onto(first.name, second.name)
        assert before != after
        assert before.index(first.name) != after.index(first.name)
