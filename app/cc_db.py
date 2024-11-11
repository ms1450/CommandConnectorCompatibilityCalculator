"""
Author: Ian Young
Purpose: To store serialized data inside memory to prevent unnecessary
compute when running against the same file.
"""

import pandas as pd
from typing import List, Dict, Union
from sqlalchemy import create_engine, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy.types import JSON
from sqlalchemy.exc import SQLAlchemyError

from app import log

# Initialize & create the SQLite in-memory database
engine = create_engine("sqlite:///:memory:", echo=True)
Base = declarative_base()
session = sessionmaker(bind=engine)()


class Files(Base):
    __tablename__ = "csv_files"

    site_name: Mapped[str] = mapped_column(
        String, primary_key=True, unique=True
    )
    csv_name: Mapped[str] = mapped_column(String)
    results: Mapped["Results"] = relationship("Results", back_populates="file")


class Results(Base):
    __tablename__ = "calculated_results"

    site_name: Mapped[str] = mapped_column(
        ForeignKey("csv_files.site_name", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
    )
    file: Mapped["Files"] = relationship("Files", back_populates="results")
    excess_channels: Mapped[int] = mapped_column(Integer)
    recommended: Mapped[List[str]] = mapped_column(JSON)  # Store list as JSON
    cameras: Mapped[str] = mapped_column(Text)  # Store DataFrame as string


# Create the tables if they do not already exist.
Base.metadata.create_all(engine)


def serialize_dataframe(df: pd.DataFrame) -> str:
    """Serialize a Pandas DataFrame to JSON

    Args:
        df (pandas.DataFrame): The Pandas DataFrame to serialize.

    Returns:
        str: JSON-serialized DataFrame.
    """
    try:
        return df.to_json(orient="split")
    except ValueError as e:
        raise ValueError("Error serializing DataFrame.") from e


def deserialize_dataframe(df_json: str) -> pd.DataFrame:
    """Deserialize a JSON-serialized DataFrame

    Args:
        df_json (str): The JSON-serialized DataFrame to deserialize.

    Returns:
        pandas.DataFrame: Pandas dataframe.
    """
    try:
        return pd.read_json(df_json, orient="split")
    except ValueError as e:
        raise ValueError("Error deserializing DataFrame.") from e


def add_file_results(file_data: dict, results_data: dict):
    """Update the tables with new data.

    Add new dictionary data to the in-memory SQLite tables.

    Args:
        file_data (dict): Dictionary information about the csv file.
        results_data (dict): Dictionary results of the calculated output.

    Returns:
        None
    """
    try:
        # Load the dictionaries into the table
        file = Files(**file_data)
        result = Results(
            site_name=file_data["site_name"],  # Map to the same site
            excess_channels=results_data.get("excess_channels", 0),
            recommended=results_data.get("recommended", []),
            cameras=results_data.get("cameras", ""),
        )

        session.add(file)
        session.commit()  # Commit the changes

        session.add(result)
        session.commit()  # Commit the changes
    except SQLAlchemyError as e:
        session.rollback()  # Undo changes
        log.error(f"An error occurred while adding file and result: {e}")


def validate_recommended_field(recommended: List[str]) -> List[str]:
    """Validates the recommended data before adding it to the SQLite table

    Args:
        recommended (list): The list to validate.

    Returns:
        list: Returns the same list that was passed through.
    """
    if not isinstance(recommended, list):
        raise ValueError("'recommended' must be a list of strings")
    if not all(isinstance(item, str) for item in recommended):
        raise ValueError("All items in 'recommended' must be strings.")
    return recommended


def update_recommendations(recommendations: List[str], excess: int, site: str):
    """Update the table information with new recommended values

    This is to be called after re-running the calculations with the
    recommendations checkbox active.

    Args:
        recommendations (list): The list of recommended connectors.
        excess (int): How many excess channels were caluclated.
        site (str): The site key value to access and upadte.

    Returns:
        None
    """
    try:
        if (
            result := session.query(Results)
            .filter(Results.site_name == site)
            .first()
        ):
            validated = validate_recommended_field(recommendations)
            result.recommended = validated
            result.excess_channels = excess

            session.commit()  # Commit changes to the table
        else:
            log.warning("Results for site '%s' not found", site)
    except SQLAlchemyError as e:
        session.rollback()  # Undo changes
        log.error(
            "An error occurred while updating results for %s: %s", site, e
        )


def get_file_results(site: str) -> Dict[str, Union[str, int]]:
    """Retrieves the calculated data for the selected site

    Args:
        site (str): The site name to retrieve data for.

    Returns:
        dict: A dictinoary of the data associated with the site.
    """
    if (
        result := session.query(Results)
        .filter(Results.site_name == site)
        .first()
    ):
        return {
            "site_name": result.site_name,
            "excess_channels": result.excess_channels,
            "recommended": result.recommended,
            "cameras": result.cameras,
        }
    log.warning("No results were found.")
    return {}


def file_exists(file_name):
    """Returns a boolean value if a file exists in the database.

    Returns a boolean value indicating whether a csv file with the same
    name exists in the database.
    #! Failed edge-case is if there are two files with the same name but
    #! different site names.

    Args:
        file_name (str): The csv file name to check if it exists in the database.

    Returns:
        bool: Boolean value indicating True or False on a file existing
            in the database.
    """
    if (
        exists := session.query(Files)
        .filter(Files.csv_name == file_name)
        .first()
    ):
        log.info("Found %s", exists)
        return True
    return False


def close_session():
    """Closes the current session and engine; erases all data"""
    session.close()
