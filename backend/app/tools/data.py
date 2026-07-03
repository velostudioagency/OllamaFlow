import json
import re
from pathlib import Path
from typing import Any, Dict

from app.core.config import WORKSPACE_DIR


def csv_analyze(file_path: str, operation: str = "summary", column: str = "",
                filter_value: str = "", limit: int = 20, **kwargs) -> str:
    try:
        import pandas as pd
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(WORKSPACE_DIR) / file_path
        if not path.exists():
            return f"Error: File not found: {file_path}"
        df = pd.read_csv(str(path))
        if operation == "summary":
            buf = []
            buf.append(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
            buf.append(f"\nColumns: {', '.join(df.columns.tolist())}")
            buf.append(f"\nData types:\n{df.dtypes.to_string()}")
            buf.append(f"\nBasic stats:\n{df.describe().to_string()}")
            buf.append(f"\nNull counts:\n{df.isnull().sum().to_string()}")
            return "\n".join(buf)[:10000]
        elif operation == "head":
            return df.head(limit).to_string()[:10000]
        elif operation == "filter" and column and filter_value:
            try:
                filtered = df[df[column].astype(str).str.contains(filter_value, case=False, na=False)]
            except Exception:
                filtered = df[df[column] == filter_value]
            return f"Filtered ({len(filtered)} rows):\n{filtered.head(limit).to_string()}"[:10000]
        elif operation == "sort" and column:
            ascending = not filter_value.lower().startswith("desc")
            sorted_df = df.sort_values(by=column, ascending=ascending)
            return sorted_df.head(limit).to_string()[:10000]
        elif operation == "group" and column:
            grouped = df.groupby(column).size().reset_index(name="count")
            grouped = grouped.sort_values("count", ascending=False)
            return grouped.head(limit).to_string()[:10000]
        else:
            return f"Error: Invalid operation '{operation}' or missing column parameter"
    except ImportError:
        return "Error: pandas not installed"
    except Exception as e:
        return f"Error analyzing CSV: {str(e)}"


def database_query(db_path: str, query: str, params: str = "", **kwargs) -> str:
    try:
        import sqlite3
        path = Path(db_path)
        if not path.is_absolute():
            path = Path(WORKSPACE_DIR) / db_path
        if not path.exists():
            return f"Error: Database not found: {db_path}"
        bind_params = []
        if params:
            try:
                bind_params = json.loads(params) if isinstance(params, str) else params
            except Exception:
                pass
        conn = sqlite3.connect(str(path))
        try:
            cursor = conn.cursor()
            if bind_params:
                cursor.execute(query, bind_params)
            else:
                cursor.execute(query)
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER")):
                conn.commit()
                return f"Query executed. Rows affected: {cursor.rowcount}"
            rows = cursor.fetchall()
            if not rows:
                return "Query returned no results."
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            lines = [" | ".join(str(c) for c in col_names)]
            lines.append("-" * len(lines[0]))
            for row in rows[:100]:
                lines.append(" | ".join(str(v) for v in row))
            result = "\n".join(lines)
            if len(rows) > 100:
                result += f"\n... ({len(rows) - 100} more rows)"
            return result[:10000]
        finally:
            conn.close()
    except Exception as e:
        return f"Database error: {str(e)}"


def json_query(data: str, query: str, **kwargs) -> str:
    try:
        if isinstance(data, str):
            parsed = json.loads(data)
        else:
            parsed = data
        parts = [p for p in re.split(r'\.(?![^\[]*\])', query) if p]
        current = parsed
        for part in parts:
            array_match = re.match(r'^(\w+)\[(\d+)\]$', part)
            if array_match:
                key = array_match.group(1)
                idx = int(array_match.group(2))
                if isinstance(current, dict):
                    current = current[key]
                current = current[idx]
            elif isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                current = current[int(part)]
            else:
                return f"Error: Cannot navigate into {type(current).__name__} with key '{part}'"
        if isinstance(current, (dict, list)):
            return json.dumps(current, indent=2, ensure_ascii=False)[:10000]
        return str(current)
    except (KeyError, IndexError, TypeError) as e:
        return f"Error: Query '{query}' failed - {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"
    except Exception as e:
        return f"Error: {str(e)}"


def markitdown_convert(file_path: str = "", input_type: str = "local_file", url: str = "",
                       use_llm: bool = False, llm_model: str = "", **kwargs) -> str:
    try:
        from markitdown import MarkItDown
        kwargs_markitdown = {}
        if use_llm and llm_model:
            from openai import OpenAI
            kwargs_markitdown["llm_client"] = OpenAI()
            kwargs_markitdown["llm_model"] = llm_model

        md = MarkItDown(**kwargs_markitdown)

        if input_type == "url" and url:
            result = md.convert_url(url)
        elif file_path:
            path = Path(file_path)
            if not path.is_absolute():
                path = Path(WORKSPACE_DIR) / file_path
            if not path.exists():
                return f"Error: File not found: {file_path}"
            result = md.convert(str(path))
        else:
            return "Error: Provide file_path or url"

        return result.text_content[:10000]
    except ImportError as e:
        return f"Error: markitdown not installed. Run: pip install markitdown[all]. Details: {e}"
    except Exception as e:
        return f"MarkItDown error: {str(e)}"
