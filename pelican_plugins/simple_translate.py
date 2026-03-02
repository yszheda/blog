from pelican import signals


def add_translation_function(generator):
    # Add a simple translation function that returns the input
    generator.context["_"] = lambda x: x


def register():
    signals.generator_init.connect(add_translation_function)
