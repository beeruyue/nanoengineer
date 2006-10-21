/*
  Name: boxtree.cpp
  Copyright: 2006 Nanorex, Inc.  All rights reserved.
  Author: Oleksandr Shevchenko
  Description: class for boxtree representation  
*/

#include "boxtree.h"

//----------------------------------------------------------------------------
// mNumber

int BoxTree::Number;					// max number of elements in box

//----------------------------------------------------------------------------
// mBase

Box * BoxTree::Base;					// base for boxes pointers

//----------------------------------------------------------------------------
// Constructor

BoxTree::BoxTree():
	mLeft(								// first leaf for tree
		0),
	mRight(								// second leaf for tree
		0)
{

}

//----------------------------------------------------------------------------
// Destructor

BoxTree::~BoxTree()
{

}

//----------------------------------------------------------------------------
// Add()
//
// add box into container
//
void BoxTree::Add(
	Box * box)
{
	mBoxes.Add(box);
	mBox.Enclose(box->Min());
	mBox.Enclose(box->Max());
}

//----------------------------------------------------------------------------
// BestAxe()
//
// best split axe
//
int BoxTree::BestAxe()
{
	int lx = 0;
	int rx = 0;
	int ly = 0;
	int ry = 0;
	int lz = 0;
	int rz = 0;
	int n = Size();
	for (int i=0; i<n; i++)
	{
		Triple center = mBoxes[i]->Center() - mBox.Center();
		if (center.X()<0) lx++; else rx++;
		if (center.Y()<0) ly++; else ry++;
		if (center.Z()<0) lz++; else rz++;
	}
	int x_break = (lx != 0 && rx != 0);
	int y_break = (ly != 0 && ry != 0);
	int z_break = (lz != 0 && rz != 0);
	Triple d = mBox.Extent();
	if (x_break)
	{
		if (y_break)
		{
			if (z_break)
			{
				if (d.X()>d.Y())
				{
					if (d.X()>d.Z())
						return (3);
					else
						return (1);
				}
				else
				{
					if (d.Y()>d.Z())
						return (2);
					else
						return (1);
				}
			}
			else
			{
				if (d.X()>d.Y())
					return (3);
				else
					return (2);
			}
		}
		else
		{
			if (z_break)
			{
				if (d.X()>d.Z())
					return (3);
				else
					return (1);
			}
			else
			{
				return (3);
			}
		}
	}
	else
	{
		if (y_break)
		{
			if (z_break)
			{
				if (d.Y()>d.Z())
					return (2);
				else
					return (1);
			}
			else
			{
				return (2);
			}
		}
		else
		{
			if (z_break)
			{
				return (1);
			}
			else
			{
				return (0);
			}
		}
	}
}

//----------------------------------------------------------------------------
// BuildTree()
//
// create bounding volume box tree
//
int BoxTree::BuildTree()
{
	int i;
	if (Empty()) i = Split();
	if (!i) return 0;
	if (Empty()) return 1;
	if (Left()) i = Left()->BuildTree();
	if (!i) return 0;
	if (Right()) i = Right()->BuildTree();
	if (!i) return 0;
	return 1;
}

//----------------------------------------------------------------------------
// Delete()
//
// recursive delete
//
void BoxTree::Delete(
	BoxTree * tree)
{
	if (tree)
	{
		Delete(tree->Left());
		Delete(tree->Right());
		tree->DeleteLeaf();
	}
}

//----------------------------------------------------------------------------
// Duplicate()
//
// delete duplicate entities
//
void BoxTree::Duplicate(
	int * ia)
{
	Duplicate(ia,this);
}

//----------------------------------------------------------------------------
// Duplicate()
//
// delete duplicate entities
//
void BoxTree::Duplicate(
	int * ia,
	BoxTree * bt)
{
	if (bt)
	{
		if (!(bt->Left() && bt->Right()))
		{
			for (int il=0; il<bt->mBoxes.Size(); il++)
			{
				Box * bi = bt->mBoxes[il];
				int i = int(bi - Base);
				for (int jl=il+1; jl<bt->mBoxes.Size(); jl++)
				{
					Box * bj = bt->mBoxes[jl];
					int j = int(bj - Base);
					if (ia[j]>0)
					{
						ia[j] = -ia[i];
					}
				}
			}
		}
		Duplicate(ia,bt->Left());
		Duplicate(ia,bt->Right());
	}
}

//----------------------------------------------------------------------------
// Initialize()
//
// formation of main box
//
int BoxTree::Initialize(
	const Container<Box *> & boxes)
{
	int n = boxes.Size();
	for (int i=0; i<n; i++)
	{
		Add(boxes[i]);
	}
	return (BuildTree());
}

//----------------------------------------------------------------------------
// Split()
//
// split box
//
int BoxTree::Split()
{
	int i;
	int n = Size();
	if (n<=Number) return 1;
	//  best split axe
	int variant = BestAxe();
	//  now we can subdivide
	if(!AllocateTree()) return 0;
	//  put entities into boxes
	for (i=0; i<n; i++)
	{
		switch (WhichBox(variant,i))
		{
		case 0:
			Left()->Add(mBoxes[i]);
			break;
		case 1:
			Right()->Add(mBoxes[i]);
			break;
		}
	}
	//  calculate new subboxes
	if (Left()->Size() && Right()->Size())
	{
		mBoxes.Empty();
	}
	else
	{
		FreeTree();
	}
	return 1;
}
