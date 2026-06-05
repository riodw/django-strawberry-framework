# TODO(spec-029 Slice 2): Add fakeshop call_command coverage for inspect_django_type.
# Pseudo:
#   def _reload_inspect_schema():
#       registry.clear()
#       reload apps.library.schema
#       reload config.schema
#
#   def test_inspect_by_registered_name(_reload_inspect_schema):
#       out = StringIO()
#       call_command("inspect_django_type", "BookType", stdout=out)
#       assert "id" and "Int!" in out.getvalue()
#       assert "subtitle" and "String" in out.getvalue()
#       assert "circulation_status" and "choice enum" in out.getvalue()
#
#   def test_inspect_with_schema_option_cold_path():
#       registry.clear()
#       call_command("inspect_django_type", "BookType", "--schema", "config.schema")
#       call_command("inspect_django_type", "BookType", "--schema", "config.schema:schema")
#
#   def test_inspect_relay_node_pk_row(_reload_inspect_schema):
#       call_command("inspect_django_type", "GenreType")
#       assert "GlobalID!" and "relay.Node id" in stdout
#
#   def test_inspect_reads_resolved_annotation_not_field_null(_reload_inspect_schema):
#       call_command("inspect_django_type", "NullabilityOverrideBookType")
#       assert title reports String and subtitle reports String!
