# TODO(spec-029 Slice 2): Add package-internal failure-mode coverage for inspect_django_type.
# Pseudo:
#   def test_bad_dotted_path_raises_command_error():
#       call_command("inspect_django_type", "does.not.exist.Type")
#
#   def test_ambiguous_bare_name_raises_command_error():
#       register two DjangoType classes with __name__ == "BookType"
#       call_command("inspect_django_type", "BookType")
#       assert CommandError lists module.qualname candidates
#
#   def test_non_djangotype_symbol_raises_command_error():
#       call_command("inspect_django_type", "test_module.not_a_type")
#
#   def test_abstract_base_without_definition_raises_command_error():
#       class Abstract(DjangoType): pass
#       call_command("inspect_django_type", dotted path to Abstract)
#
#   def test_unfinalized_type_raises_command_error():
#       define concrete DjangoType without finalizing registry
#       call_command("inspect_django_type", dotted path)
#       assert CommandError names --schema / finalize_django_types()
