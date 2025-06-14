
def format_subnodes(subnodes, indent=0):
        lines = []
        for key, value in subnodes.items():
            lines.append('    ' * indent + f'- {key}')
            if isinstance(value, dict) and value:
                lines.extend(format_subnodes(value, indent + 1))
        return lines